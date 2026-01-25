# services/url_extractor.py
"""
URL Content Extractor Service
Extracts predictions from ANY URL:
- News articles (CNN, BBC, CNBC, Bloomberg, Reuters, etc.)
- YouTube videos (with transcript extraction)
- Twitter/X posts
- Reddit posts
- Substack newsletters
- Medium articles
- Podcasts (Spotify, Apple - metadata)
- LinkedIn posts
- Any blog or website
"""
import os
import re
import httpx
import logging
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from anthropic import Anthropic
from html.parser import HTMLParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import youtube_transcript_api for better YouTube support
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    YOUTUBE_TRANSCRIPT_AVAILABLE = True
except ImportError:
    YOUTUBE_TRANSCRIPT_AVAILABLE = False
    logger.info("youtube-transcript-api not installed - YouTube transcripts will be limited")


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
        url_lower = url.lower()
        
        # Video platforms
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        if 'vimeo.com' in url_lower:
            return 'vimeo'
        if 'tiktok.com' in url_lower:
            return 'tiktok'
        
        # Social media
        if 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        if 'reddit.com' in url_lower:
            return 'reddit'
        if 'linkedin.com' in url_lower:
            return 'linkedin'
        if 'facebook.com' in url_lower or 'fb.com' in url_lower:
            return 'facebook'
        if 'instagram.com' in url_lower:
            return 'instagram'
        if 'threads.net' in url_lower:
            return 'threads'
        
        # Podcasts
        if 'podcasts.apple.com' in url_lower:
            return 'apple_podcast'
        if 'spotify.com' in url_lower and '/episode' in url_lower:
            return 'spotify_podcast'
        if 'spotify.com' in url_lower:
            return 'spotify'
        
        # Newsletter/Blog platforms
        if 'substack.com' in url_lower:
            return 'substack'
        if 'medium.com' in url_lower:
            return 'medium'
        if 'mirror.xyz' in url_lower:
            return 'mirror'
        
        # News sites (special handling for paywalls)
        if any(site in url_lower for site in ['wsj.com', 'ft.com', 'economist.com', 'nytimes.com', 'washingtonpost.com']):
            return 'paywall_news'
        
        # General article
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
        """Fetch YouTube video info and FULL transcript"""
        video_id = self._extract_youtube_id(url)
        if not video_id:
            return {"error": "Invalid YouTube URL"}
        
        content_parts = []
        title = ""
        author = ""
        
        # Try to get video info from oEmbed (no API key needed)
        try:
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            response = await self.client.get(oembed_url)
            if response.status_code == 200:
                data = response.json()
                title = data.get("title", "")
                author = data.get("author_name", "")
                content_parts.append(f"Video Title: {title}")
                content_parts.append(f"Channel/Speaker: {author}")
        except Exception as e:
            logger.debug(f"Could not get YouTube oEmbed: {e}")
        
        # Try to get FULL transcript using youtube-transcript-api
        if YOUTUBE_TRANSCRIPT_AVAILABLE:
            try:
                # Get transcript (tries multiple languages)
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # Try to get English transcript first, then any available
                transcript = None
                try:
                    transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
                except:
                    try:
                        # Get auto-generated or first available
                        transcript = transcript_list.find_generated_transcript(['en'])
                    except:
                        # Get any transcript and translate to English
                        for t in transcript_list:
                            transcript = t.translate('en')
                            break
                
                if transcript:
                    transcript_data = transcript.fetch()
                    # Combine transcript text
                    full_text = " ".join([item['text'] for item in transcript_data])
                    # Limit to reasonable size but keep enough for context
                    full_text = full_text[:20000] if len(full_text) > 20000 else full_text
                    content_parts.append(f"\n--- FULL VIDEO TRANSCRIPT ---\n{full_text}\n--- END TRANSCRIPT ---")
                    logger.info(f"Got YouTube transcript: {len(full_text)} chars")
            except Exception as e:
                logger.debug(f"Could not get YouTube transcript: {e}")
        
        # Fallback: Try to get description from page
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            response = await self.client.get(video_url)
            
            if response.status_code == 200:
                # Look for description in page
                desc_match = re.search(r'"description":{"simpleText":"([^"]+)"', response.text)
                if desc_match:
                    description = desc_match.group(1).replace('\\n', '\n')
                    content_parts.append(f"\nVideo Description: {description[:3000]}")
        except Exception as e:
            logger.debug(f"Could not fetch YouTube page: {e}")
        
        if not content_parts:
            return {"error": "Could not extract YouTube content. Try providing the video's transcript manually."}
        
        return {
            "title": title,
            "content": "\n\n".join(content_parts),
            "url": url,
            "type": "youtube",
            "author": author
        }
    
    async def _fetch_twitter_content(self, url: str) -> Dict:
        """Fetch Twitter/X post content"""
        # Extract tweet info using nitter or other methods
        try:
            # Try using a public nitter instance (Twitter frontend alternative)
            nitter_instances = [
                "nitter.net",
                "nitter.unixfox.eu",
            ]
            
            # Convert twitter URL to nitter format
            tweet_path = url.split('twitter.com')[-1] if 'twitter.com' in url else url.split('x.com')[-1]
            
            for instance in nitter_instances:
                try:
                    nitter_url = f"https://{instance}{tweet_path}"
                    response = await self.client.get(nitter_url, timeout=10)
                    if response.status_code == 200:
                        # Extract tweet content
                        parser = TextExtractor()
                        parser.feed(response.text)
                        content = " ".join(parser.text)
                        
                        return {
                            "title": f"Tweet",
                            "content": content[:5000],
                            "url": url,
                            "type": "twitter"
                        }
                except:
                    continue
            
            # Fallback: Just note it's a Twitter URL
            return {
                "title": "Twitter/X Post",
                "content": f"Twitter URL: {url}\n\n[Please paste the tweet text manually if extraction failed]",
                "url": url,
                "type": "twitter"
            }
        except Exception as e:
            return {"error": f"Could not extract Twitter content: {e}"}
    
    async def _fetch_reddit_content(self, url: str) -> Dict:
        """Fetch Reddit post content using JSON API"""
        try:
            # Reddit provides JSON by appending .json
            json_url = url.rstrip('/') + '.json'
            
            response = await self.client.get(json_url, headers={
                'User-Agent': 'TrackRecord/1.0'
            })
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    post = data[0]['data']['children'][0]['data']
                    title = post.get('title', '')
                    selftext = post.get('selftext', '')
                    author = post.get('author', '')
                    subreddit = post.get('subreddit', '')
                    
                    content_parts = [
                        f"Title: {title}",
                        f"Author: u/{author}",
                        f"Subreddit: r/{subreddit}",
                        f"\nContent:\n{selftext}"
                    ]
                    
                    # Get top comments
                    if len(data) > 1:
                        comments = data[1]['data']['children'][:5]
                        comment_texts = []
                        for c in comments:
                            if c['kind'] == 't1':
                                comment_texts.append(f"- {c['data'].get('body', '')[:500]}")
                        if comment_texts:
                            content_parts.append(f"\nTop Comments:\n" + "\n".join(comment_texts))
                    
                    return {
                        "title": title,
                        "content": "\n".join(content_parts),
                        "url": url,
                        "type": "reddit",
                        "author": author
                    }
            
            return {"error": "Could not fetch Reddit content"}
        except Exception as e:
            return {"error": f"Reddit extraction failed: {e}"}
    
    async def _fetch_substack_content(self, url: str) -> Dict:
        """Fetch Substack newsletter content"""
        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                parser = TextExtractor()
                parser.feed(response.text)
                
                # Try to find author
                author_match = re.search(r'"author":\s*{\s*"name":\s*"([^"]+)"', response.text)
                author = author_match.group(1) if author_match else ""
                
                return {
                    "title": parser.title,
                    "content": " ".join(parser.text)[:15000],
                    "url": url,
                    "type": "substack",
                    "author": author
                }
        except Exception as e:
            return {"error": f"Substack extraction failed: {e}"}
        
        return await self._fetch_article_content(url)
    
    async def _fetch_medium_content(self, url: str) -> Dict:
        """Fetch Medium article content"""
        # Medium has good semantic HTML, use standard extraction
        return await self._fetch_article_content(url)
    
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
        Main method: Extract predictions from ANY URL
        
        Supported sources:
        - News articles (any website)
        - YouTube videos (with full transcript)
        - Twitter/X posts
        - Reddit posts
        - Substack newsletters
        - Medium articles
        - LinkedIn posts
        - And more...
        
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
        
        # Route to appropriate handler based on URL type
        handlers = {
            'youtube': self._fetch_youtube_content,
            'twitter': self._fetch_twitter_content,
            'reddit': self._fetch_reddit_content,
            'substack': self._fetch_substack_content,
            'medium': self._fetch_medium_content,
            # These all use standard article extraction
            'article': self._fetch_article_content,
            'vimeo': self._fetch_article_content,
            'linkedin': self._fetch_article_content,
            'facebook': self._fetch_article_content,
            'paywall_news': self._fetch_article_content,
            'mirror': self._fetch_article_content,
        }
        
        handler = handlers.get(url_type, self._fetch_article_content)
        content = await handler(url)
        
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
