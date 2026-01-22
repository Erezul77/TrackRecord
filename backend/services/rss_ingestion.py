# services/rss_ingestion.py
"""
RSS Feed Ingestion Service
Pulls articles from news sources and extracts predictions using AI
"""
import feedparser
import httpx
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class NewsArticle:
    title: str
    url: str
    summary: str
    published: datetime
    source: str
    author: Optional[str] = None

# News RSS feeds that often contain predictions
RSS_FEEDS = {
    # Financial News
    "cnbc_markets": {
        "url": "https://www.cnbc.com/id/10000664/device/rss/rss.html",
        "source": "CNBC Markets",
        "categories": ["markets", "economy"]
    },
    "cnbc_economy": {
        "url": "https://www.cnbc.com/id/20910258/device/rss/rss.html",
        "source": "CNBC Economy",
        "categories": ["economy"]
    },
    "bloomberg_markets": {
        "url": "https://feeds.bloomberg.com/markets/news.rss",
        "source": "Bloomberg Markets",
        "categories": ["markets"]
    },
    "reuters_business": {
        "url": "https://www.reutersagency.com/feed/?best-topics=business-finance",
        "source": "Reuters Business",
        "categories": ["markets", "economy"]
    },
    # Crypto News
    "coindesk": {
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "source": "CoinDesk",
        "categories": ["crypto"]
    },
    "cointelegraph": {
        "url": "https://cointelegraph.com/rss",
        "source": "Cointelegraph",
        "categories": ["crypto"]
    },
    # Politics/Policy
    "politico": {
        "url": "https://www.politico.com/rss/politicopicks.xml",
        "source": "Politico",
        "categories": ["politics"]
    },
    # Tech
    "techcrunch": {
        "url": "https://techcrunch.com/feed/",
        "source": "TechCrunch",
        "categories": ["tech"]
    },
}

# Known pundits and their variations in article text
KNOWN_PUNDITS = {
    "balajis": ["Balaji Srinivasan", "Balaji", "@balajis"],
    "jimcramer": ["Jim Cramer", "Cramer", "Mad Money"],
    "CathieDWood": ["Cathie Wood", "Cathie", "ARK Invest", "Ark's Cathie Wood"],
    "PeterSchiff": ["Peter Schiff", "Schiff"],
    "NateSilver538": ["Nate Silver", "FiveThirtyEight", "538"],
    "saylor": ["Michael Saylor", "Saylor", "MicroStrategy"],
    "paulkrugman": ["Paul Krugman", "Krugman"],
    "LHSummers": ["Larry Summers", "Lawrence Summers", "Summers"],
    # Add more as needed
}


class RSSIngestionService:
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
    
    def fetch_feed(self, feed_key: str) -> List[NewsArticle]:
        """Fetch and parse a single RSS feed"""
        if feed_key not in RSS_FEEDS:
            raise ValueError(f"Unknown feed: {feed_key}")
        
        feed_config = RSS_FEEDS[feed_key]
        articles = []
        
        try:
            feed = feedparser.parse(feed_config["url"])
            
            for entry in feed.entries[:20]:  # Last 20 articles
                published = datetime.now()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                
                article = NewsArticle(
                    title=entry.get('title', ''),
                    url=entry.get('link', ''),
                    summary=entry.get('summary', entry.get('description', '')),
                    published=published,
                    source=feed_config["source"],
                    author=entry.get('author', None)
                )
                articles.append(article)
                
        except Exception as e:
            print(f"Error fetching {feed_key}: {e}")
        
        return articles
    
    def fetch_all_feeds(self) -> List[NewsArticle]:
        """Fetch all configured RSS feeds"""
        all_articles = []
        for feed_key in RSS_FEEDS:
            articles = self.fetch_feed(feed_key)
            all_articles.extend(articles)
        return all_articles
    
    def find_pundit_mentions(self, text: str) -> List[str]:
        """Find which known pundits are mentioned in text"""
        mentioned = []
        text_lower = text.lower()
        
        for username, variations in KNOWN_PUNDITS.items():
            for variation in variations:
                if variation.lower() in text_lower:
                    mentioned.append(username)
                    break
        
        return mentioned
    
    def content_hash(self, url: str) -> str:
        """Generate unique hash for deduplication"""
        return hashlib.sha256(url.encode()).hexdigest()
    
    def filter_prediction_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Filter articles that likely contain predictions"""
        prediction_keywords = [
            'predict', 'forecast', 'expect', 'will be', 'going to',
            'by 2025', 'by 2026', 'by 2027', 'next year', 'next month',
            'rally', 'crash', 'surge', 'plunge', 'reach', 'hit',
            'target', 'outlook', 'projection', 'bet', 'wager',
            'bullish', 'bearish', 'bottom', 'peak', 'high', 'low'
        ]
        
        filtered = []
        for article in articles:
            text = f"{article.title} {article.summary}".lower()
            if any(keyword in text for keyword in prediction_keywords):
                filtered.append(article)
        
        return filtered


# Standalone function to test
def test_feeds():
    service = RSSIngestionService()
    
    print("Fetching RSS feeds...\n")
    articles = service.fetch_all_feeds()
    print(f"Total articles fetched: {len(articles)}\n")
    
    prediction_articles = service.filter_prediction_articles(articles)
    print(f"Articles with predictions: {len(prediction_articles)}\n")
    
    print("Sample prediction articles:")
    print("-" * 60)
    for article in prediction_articles[:5]:
        pundits = service.find_pundit_mentions(f"{article.title} {article.summary}")
        print(f"Source: {article.source}")
        print(f"Title: {article.title}")
        print(f"Pundits mentioned: {pundits if pundits else 'None detected'}")
        print(f"URL: {article.url}")
        print("-" * 60)


if __name__ == "__main__":
    test_feeds()
