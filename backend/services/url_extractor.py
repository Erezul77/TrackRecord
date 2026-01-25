# services/url_extractor.py
"""
URL Content Extractor Service
Extracts predictions from any URL - articles, YouTube videos, etc.
"""
import os
import re
import httpx
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from anthropic import Anthropic
from html.parser import HTMLParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExtractedPrediction:
    pundit_name: str
    pundit_title: str
    claim: str
    quote: str
    category: str
    timeframe: str
    confidence: str
    source_url: str


class TextExtractor(HTMLParser):
    """Extract text content from HTML"""
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip_tags = {'script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript'}
        self.skip = False
        self.title = ""
        self.in_title = False
        
    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.skip = True
        if tag == 'title':
            self.in_title = True
            
    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.skip = False
        if tag == 'title':
            self.in_title = False
            
    def handle_data(self, data):
        if self.in_title:
            self.title = data.strip()
        elif not self.skip:
            text = data.strip()
            if len(text) > 20:
                self.text.append(text)


class URLExtractor:
    """
    Extracts predictions from URLs using AI
    Supports: Articles, YouTube, and more
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        self.anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    async def close(self):
        await self.client.aclose()
    
    def _detect_url_type(self, url: str) -> str:
        """Detect what type of content the URL points to"""
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        if 'twitter.com' in url or 'x.com' in url:
            return 'twitter'
        if 'podcasts.apple.com' in url or 'spotify.com' in url:
            return 'podcast'
        return 'article'
    
    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    async def _fetch_article_content(self, url: str) -> Dict:
        """Fetch and parse article content"""
        try:
            response = await self.client.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code != 200:
                return {"error": f"Failed to fetch URL: {response.status_code}"}
            
            parser = TextExtractor()
            parser.feed(response.text)
            
            content = " ".join(parser.text)
            # Limit content length
            content = content[:15000] if len(content) > 15000 else content
            
            return {
                "title": parser.title,
                "content": content,
                "url": url
            }
        except Exception as e:
            logger.error(f"Error fetching article: {e}")
            return {"error": str(e)}
    
    async def _fetch_youtube_content(self, url: str) -> Dict:
        """Fetch YouTube video info and transcript"""
        video_id = self._extract_youtube_id(url)
        if not video_id:
            return {"error": "Invalid YouTube URL"}
        
        content_parts = []
        title = ""
        
        # Try to get video info from oEmbed (no API key needed)
        try:
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            response = await self.client.get(oembed_url)
            if response.status_code == 200:
                data = response.json()
                title = data.get("title", "")
                author = data.get("author_name", "")
                content_parts.append(f"Video Title: {title}")
                content_parts.append(f"Channel: {author}")
        except Exception as e:
            logger.debug(f"Could not get YouTube oEmbed: {e}")
        
        # Try to get transcript using youtube-transcript-api approach
        try:
            # Fetch video page to get transcript
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            response = await self.client.get(video_url)
            
            if response.status_code == 200:
                # Look for description in page
                desc_match = re.search(r'"description":{"simpleText":"([^"]+)"', response.text)
                if desc_match:
                    description = desc_match.group(1).replace('\\n', '\n')
                    content_parts.append(f"Description: {description[:2000]}")
                
                # Try to find auto-generated captions data
                # This is a simplified approach - in production you'd use youtube-transcript-api
                caption_match = re.search(r'"captionTracks":\[([^\]]+)\]', response.text)
                if caption_match:
                    content_parts.append("[Video has captions available - content extracted from description and title]")
        except Exception as e:
            logger.debug(f"Could not fetch YouTube page: {e}")
        
        if not content_parts:
            return {"error": "Could not extract YouTube content. Try providing the video's transcript or key quotes."}
        
        return {
            "title": title,
            "content": "\n\n".join(content_parts),
            "url": url,
            "type": "youtube"
        }
    
    async def _extract_with_ai(self, content: Dict) -> List[Dict]:
        """Use Claude to extract predictions from content"""
        prompt = f"""You are extracting predictions from content. Analyze this and find ANY predictions made by identifiable people.

Source URL: {content.get('url', 'Unknown')}
Title: {content.get('title', 'Unknown')}

Content:
---
{content.get('content', '')}
---

Find ALL predictions - statements about what WILL happen in the future. For each prediction:

1. pundit_name: The FULL NAME of the person making the prediction (required)
2. pundit_title: Their role/title (e.g., "CEO of Tesla", "Senator", "Economist")
3. claim: The specific prediction as a clear statement
4. quote: The exact words they used (or close paraphrase if not exact)
5. category: One of: politics, economy, markets, crypto, tech, sports, entertainment, religion, science, health, climate, geopolitics, business
6. timeframe: When this prediction should come true (e.g., "2026-12-31", "end of 2026", "within 1 year")
7. confidence: How confident they sound: certain, high, medium, low, speculative

Return ONLY a valid JSON array. Example:
[
  {{
    "pundit_name": "Elon Musk",
    "pundit_title": "Tesla CEO",
    "claim": "Tesla will achieve full self-driving by end of 2026",
    "quote": "We expect to achieve full autonomy by the end of next year",
    "category": "tech",
    "timeframe": "2026-12-31",
    "confidence": "high"
  }}
]

If no clear predictions are found, return: []
Important: Only include predictions with identifiable speakers - not anonymous sources."""

        try:
            response = self.anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=3000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            import json
            result_text = response.content[0].text
            
            # Clean up response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            predictions = json.loads(result_text.strip())
            return predictions if isinstance(predictions, list) else []
            
        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            return []
    
    async def extract_from_url(self, url: str) -> Dict:
        """
        Main method: Extract predictions from any URL
        
        Returns:
            {
                "success": bool,
                "url": str,
                "url_type": str,
                "title": str,
                "predictions": List[Dict],
                "error": str (optional)
            }
        """
        url_type = self._detect_url_type(url)
        logger.info(f"Extracting from {url_type} URL: {url}")
        
        # Fetch content based on URL type
        if url_type == 'youtube':
            content = await self._fetch_youtube_content(url)
        else:
            content = await self._fetch_article_content(url)
        
        if "error" in content:
            return {
                "success": False,
                "url": url,
                "url_type": url_type,
                "error": content["error"],
                "predictions": []
            }
        
        # Extract predictions with AI
        predictions = await self._extract_with_ai(content)
        
        # Add source URL to each prediction
        for pred in predictions:
            pred["source_url"] = url
        
        return {
            "success": True,
            "url": url,
            "url_type": url_type,
            "title": content.get("title", ""),
            "predictions": predictions,
            "predictions_found": len(predictions)
        }


# Test function
async def test_extractor():
    """Test the URL extractor"""
    extractor = URLExtractor()
    
    # Test with a news article
    test_url = "https://www.cnbc.com/2024/01/15/jim-cramer-says-nvidia-will-keep-climbing.html"
    
    try:
        result = await extractor.extract_from_url(test_url)
        print(f"Result: {result}")
    finally:
        await extractor.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_extractor())
