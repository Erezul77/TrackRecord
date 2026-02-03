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


class HeadlineExtractor(HTMLParser):
    """
    Extract only headlines, subheaders, and highlighted boxes from HTML.
    This is for prediction hub pages - we don't read full articles, only prominent text.
    """
    def __init__(self, base_url: str = ""):
        super().__init__()
        self.headlines = []  # All headers h1-h6
        self.boxes = []  # Callouts, highlights, quotes, boxes
        self.links = []  # Links to sub-articles
        self.title = ""
        self.base_url = base_url
        
        # Current parsing state
        self.skip_tags = {'script', 'style', 'nav', 'noscript', 'footer'}
        self.skip = False
        self.in_title = False
        self.in_header = False  # h1-h6
        self.in_box = False  # Callout, highlight, etc
        self.current_text = ""
        self.current_link = ""
        
        # Box-like class names that typically contain predictions
        self.box_classes = ['callout', 'highlight', 'quote', 'box', 'card', 'forecast', 
                           'prediction', 'outlook', 'insight', 'summary', 'key-point',
                           'featured', 'pullquote', 'blockquote', 'alert', 'note']
    
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        class_str = attrs_dict.get('class', '').lower()
        
        if tag in self.skip_tags:
            self.skip = True
            return
            
        if tag == 'title':
            self.in_title = True
            
        # Headers h1-h6
        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.in_header = True
            self.current_text = ""
        
        # Box/callout detection
        if any(box_class in class_str for box_class in self.box_classes):
            self.in_box = True
            self.current_text = ""
        
        # Links to articles (potential sub-pages)
        if tag == 'a':
            href = attrs_dict.get('href', '')
            if href and not href.startswith('#') and not href.startswith('javascript'):
                # Convert relative to absolute URL
                if href.startswith('/'):
                    from urllib.parse import urljoin
                    href = urljoin(self.base_url, href)
                # Only keep links to the same domain
                if self.base_url:
                    from urllib.parse import urlparse
                    base_domain = urlparse(self.base_url).netloc
                    link_domain = urlparse(href).netloc
                    if base_domain and link_domain and base_domain in link_domain:
                        self.current_link = href
    
    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.skip = False
            
        if tag == 'title':
            self.in_title = False
            
        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            if self.current_text.strip():
                self.headlines.append({
                    'level': tag,
                    'text': self.current_text.strip(),
                    'link': self.current_link if self.current_link else None
                })
            self.in_header = False
            self.current_text = ""
            self.current_link = ""
        
        if tag == 'a':
            self.current_link = ""
        
        # End of box - save content
        if self.in_box and tag in ['div', 'section', 'article', 'aside']:
            if self.current_text.strip() and len(self.current_text.strip()) > 30:
                self.boxes.append(self.current_text.strip())
            self.in_box = False
            self.current_text = ""
            
    def handle_data(self, data):
        if self.skip:
            return
            
        if self.in_title:
            self.title = data.strip()
        elif self.in_header or self.in_box:
            self.current_text += " " + data.strip()


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
    
    def _is_hub_page(self, url: str) -> bool:
        """Detect if this is a predictions hub/index page (not a single article)"""
        url_lower = url.lower()
        
        # Known institutional prediction hubs
        hub_patterns = [
            'jpmorgan.com/insights',
            'goldmansachs.com/insights',
            'blackrock.com/insights',
            'morganstanley.com/ideas',
            '/predictions', '/forecasts', '/outlook',
            '/insights/', '/research/', '/analysis/',
        ]
        
        # URL patterns suggesting a hub (ending without article slug)
        if any(pattern in url_lower for pattern in hub_patterns):
            # Check if it ends like a hub page (not an article)
            path = url.rstrip('/').split('/')[-1]
            # Article URLs usually have long slugs or dates
            if len(path) < 30 and not re.search(r'\d{4}', path):
                return True
        
        return False
    
    async def _fetch_hub_headlines(self, url: str) -> Dict:
        """
        Fetch ONLY headlines and boxes from a hub/index page.
        No full article reading - just headers, subheaders, and highlighted boxes.
        """
        try:
            response = await self.client.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code != 200:
                return {"error": f"Failed to fetch URL: {response.status_code}"}
            
            parser = HeadlineExtractor(base_url=url)
            parser.feed(response.text)
            
            # Combine headlines and boxes into content
            content_parts = [f"Page Title: {parser.title}", "\n--- HEADLINES ---"]
            
            for h in parser.headlines:
                prefix = "##" if h['level'] in ['h1', 'h2'] else "###"
                content_parts.append(f"{prefix} {h['text']}")
            
            if parser.boxes:
                content_parts.append("\n--- HIGHLIGHTED CONTENT ---")
                for box in parser.boxes[:20]:  # Limit to 20 boxes
                    content_parts.append(f"• {box[:500]}")  # Limit each box
            
            # Get sub-article links for potential follow-up
            sub_links = []
            for h in parser.headlines:
                if h.get('link'):
                    sub_links.append(h['link'])
            
            logger.info(f"Hub page: {len(parser.headlines)} headlines, {len(parser.boxes)} boxes, {len(sub_links)} sub-links")
            
            return {
                "title": parser.title,
                "content": "\n".join(content_parts),
                "url": url,
                "type": "hub_page",
                "sub_links": sub_links[:10],  # Return up to 10 sub-article links
                "headline_count": len(parser.headlines),
                "box_count": len(parser.boxes)
            }
        except Exception as e:
            logger.error(f"Error fetching hub page: {e}")
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
        
        is_hub = content.get('type') == 'hub_page'
        
        if is_hub:
            # Special prompt for hub pages - focus on headlines
            prompt = f"""You are extracting predictions from an INSTITUTIONAL PREDICTIONS PAGE (like JPMorgan, Goldman Sachs).

Source URL: {content.get('url', 'Unknown')}
Title: {content.get('title', 'Unknown')}

HEADLINES AND HIGHLIGHTED CONTENT:
---
{content.get('content', '')}
---

IMPORTANT: These are headlines and highlighted boxes from a predictions/forecasts hub page.
- Assume the predictions are made by the INSTITUTION (e.g., "JPMorgan", "Goldman Sachs")
- Or extract the specific analyst name if mentioned

For each prediction headline, extract:
1. pundit_name: Institution name OR analyst name (e.g., "JPMorgan", "Goldman Sachs", "Jamie Dimon")
2. pundit_title: Role (e.g., "Research Team", "Chief Economist", "Global Strategist")
3. claim: The prediction - be specific with numbers/targets
4. quote: The headline or highlighted text
5. category: One of: economy, markets, crypto, tech, geopolitics, business
6. timeframe: Year/date mentioned (e.g., "2026-12-31", "Q2 2026")
7. confidence: high (institutions are usually confident)

ONLY extract FUTURE predictions (not past events or current facts).

Return ONLY a valid JSON array. Example:
[
  {{
    "pundit_name": "JPMorgan",
    "pundit_title": "Research Team",
    "claim": "S&P 500 will reach 6,000 by end of 2026",
    "quote": "S&P 500 Target: 6,000",
    "category": "markets",
    "timeframe": "2026-12-31",
    "confidence": "high"
  }}
]

If no clear predictions, return: []"""
        else:
            # Standard prompt for articles
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
        - Prediction hub pages (JPMorgan, Goldman, etc.) - headlines only
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
                "sub_links": List[str] (for hub pages),
                "error": str (optional)
            }
        """
        url_type = self._detect_url_type(url)
        is_hub = self._is_hub_page(url)
        
        if is_hub:
            url_type = "hub_page"
        
        logger.info(f"Extracting from {url_type} URL: {url}")
        
        # Route to appropriate handler based on URL type
        handlers = {
            'hub_page': self._fetch_hub_headlines,  # NEW: Headlines only for hubs
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
        
        result = {
            "success": True,
            "url": url,
            "url_type": url_type,
            "title": content.get("title", ""),
            "predictions": predictions,
            "predictions_found": len(predictions)
        }
        
        # For hub pages, include sub-links for potential follow-up
        if is_hub and content.get("sub_links"):
            result["sub_links"] = content["sub_links"]
            result["note"] = f"Found {len(content['sub_links'])} sub-article links. You can extract from those individually for more predictions."
        
        return result


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
