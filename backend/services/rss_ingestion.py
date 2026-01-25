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
    # ===== FINANCIAL NEWS =====
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
    
    # ===== CRYPTO NEWS =====
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
    
    # ===== POLITICS NEWS =====
    "politico": {
        "url": "https://www.politico.com/rss/politicopicks.xml",
        "source": "Politico",
        "categories": ["politics"]
    },
    "hill": {
        "url": "https://thehill.com/feed/",
        "source": "The Hill",
        "categories": ["politics"]
    },
    "axios": {
        "url": "https://api.axios.com/feed/",
        "source": "Axios",
        "categories": ["politics", "tech"]
    },
    "npr_politics": {
        "url": "https://feeds.npr.org/1014/rss.xml",
        "source": "NPR Politics",
        "categories": ["politics"]
    },
    "bbc_world": {
        "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "source": "BBC World",
        "categories": ["politics", "geopolitics"]
    },
    
    # ===== TECH NEWS =====
    "techcrunch": {
        "url": "https://techcrunch.com/feed/",
        "source": "TechCrunch",
        "categories": ["tech"]
    },
    "verge": {
        "url": "https://www.theverge.com/rss/index.xml",
        "source": "The Verge",
        "categories": ["tech", "entertainment"]
    },
    "wired": {
        "url": "https://www.wired.com/feed/rss",
        "source": "Wired",
        "categories": ["tech", "science"]
    },
    
    # ===== SPORTS NEWS =====
    "espn": {
        "url": "https://www.espn.com/espn/rss/news",
        "source": "ESPN",
        "categories": ["sports"]
    },
    "espn_nfl": {
        "url": "https://www.espn.com/espn/rss/nfl/news",
        "source": "ESPN NFL",
        "categories": ["sports"]
    },
    "espn_nba": {
        "url": "https://www.espn.com/espn/rss/nba/news",
        "source": "ESPN NBA",
        "categories": ["sports"]
    },
    "bleacher_report": {
        "url": "https://bleacherreport.com/articles/feed",
        "source": "Bleacher Report",
        "categories": ["sports"]
    },
    "athletic": {
        "url": "https://theathletic.com/feeds/rss/news/",
        "source": "The Athletic",
        "categories": ["sports"]
    },
    
    # ===== ENTERTAINMENT NEWS =====
    "variety": {
        "url": "https://variety.com/feed/",
        "source": "Variety",
        "categories": ["entertainment", "media"]
    },
    "hollywood_reporter": {
        "url": "https://www.hollywoodreporter.com/feed/",
        "source": "Hollywood Reporter",
        "categories": ["entertainment", "media"]
    },
    "deadline": {
        "url": "https://deadline.com/feed/",
        "source": "Deadline",
        "categories": ["entertainment", "media"]
    },
    "billboard": {
        "url": "https://www.billboard.com/feed/",
        "source": "Billboard",
        "categories": ["entertainment"]
    },
    
    # ===== SCIENCE & HEALTH NEWS =====
    "science_daily": {
        "url": "https://www.sciencedaily.com/rss/all.xml",
        "source": "Science Daily",
        "categories": ["science"]
    },
    "nature": {
        "url": "http://feeds.nature.com/nature/rss/current",
        "source": "Nature",
        "categories": ["science"]
    },
    "stat_news": {
        "url": "https://www.statnews.com/feed/",
        "source": "STAT News",
        "categories": ["health", "science"]
    },
    "medical_news": {
        "url": "https://www.medicalnewstoday.com/rss",
        "source": "Medical News Today",
        "categories": ["health"]
    },
    
    # ===== CLIMATE & ENVIRONMENT =====
    "climate_home": {
        "url": "https://www.climatechangenews.com/feed/",
        "source": "Climate Home News",
        "categories": ["climate", "science"]
    },
    "carbon_brief": {
        "url": "https://www.carbonbrief.org/feed/",
        "source": "Carbon Brief",
        "categories": ["climate", "science"]
    },
    
    # ===== GEOPOLITICS =====
    "foreign_policy": {
        "url": "https://foreignpolicy.com/feed/",
        "source": "Foreign Policy",
        "categories": ["geopolitics", "politics"]
    },
    "al_jazeera": {
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "source": "Al Jazeera",
        "categories": ["geopolitics", "politics"]
    },
}

# Known pundits and their variations in article text
KNOWN_PUNDITS = {
    # ===== FINANCE & CRYPTO =====
    "balajis": ["Balaji Srinivasan", "Balaji", "@balajis"],
    "jimcramer": ["Jim Cramer", "Cramer", "Mad Money"],
    "CathieDWood": ["Cathie Wood", "Cathie", "ARK Invest", "Ark's Cathie Wood"],
    "PeterSchiff": ["Peter Schiff", "Schiff"],
    "saylor": ["Michael Saylor", "Saylor", "MicroStrategy"],
    "paulkrugman": ["Paul Krugman", "Krugman"],
    "LHSummers": ["Larry Summers", "Lawrence Summers", "Summers"],
    "elonmusk": ["Elon Musk", "Musk", "Tesla CEO", "SpaceX CEO"],
    "RayDalio": ["Ray Dalio", "Dalio", "Bridgewater"],
    "BillAckman": ["Bill Ackman", "Ackman", "Pershing Square"],
    
    # ===== POLITICS =====
    "realDonaldTrump": ["Donald Trump", "Trump", "President Trump", "former President Trump"],
    "JoeBiden": ["Joe Biden", "Biden", "President Biden"],
    "BernieSanders": ["Bernie Sanders", "Sanders", "Senator Sanders"],
    "AOC": ["Alexandria Ocasio-Cortez", "AOC", "Ocasio-Cortez"],
    "tedcruz": ["Ted Cruz", "Cruz", "Senator Cruz"],
    "GovRonDeSantis": ["Ron DeSantis", "DeSantis", "Governor DeSantis"],
    "GavinNewsom": ["Gavin Newsom", "Newsom", "Governor Newsom"],
    "netanyahu": ["Benjamin Netanyahu", "Netanyahu", "Bibi"],
    "EmmanuelMacron": ["Emmanuel Macron", "Macron", "President Macron"],
    "JMilei": ["Javier Milei", "Milei"],
    
    # ===== SPORTS =====
    "NateSilver538": ["Nate Silver", "FiveThirtyEight", "538"],
    "stephenasmith": ["Stephen A. Smith", "Stephen A", "First Take"],
    "RealSkipBayless": ["Skip Bayless", "Skip", "Undisputed"],
    "ShannonSharpe": ["Shannon Sharpe", "Sharpe"],
    "BillSimmons": ["Bill Simmons", "Simmons", "The Ringer"],
    
    # ===== ENTERTAINMENT =====
    "ScottMendelson": ["Scott Mendelson", "Mendelson"],
    
    # ===== SCIENCE & HEALTH =====
    "neiltyson": ["Neil deGrasse Tyson", "Neil Tyson", "deGrasse Tyson"],
    "EricTopol": ["Eric Topol", "Topol"],
    "MichaelEMann": ["Michael Mann", "climate scientist Mann"],
    
    # ===== GEOPOLITICS =====
    "ianbremmer": ["Ian Bremmer", "Bremmer", "Eurasia Group"],
    "PeterZeihan": ["Peter Zeihan", "Zeihan"],
    
    # ===== MEDIA COMMENTATORS =====
    "benshapiro": ["Ben Shapiro", "Shapiro", "Daily Wire"],
    "TuckerCarlson": ["Tucker Carlson", "Tucker"],
    "joerogan": ["Joe Rogan", "Rogan", "JRE"],
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
            # Financial
            'predict', 'forecast', 'expect', 'will be', 'going to',
            'by 2025', 'by 2026', 'by 2027', 'by 2028', 'by 2030',
            'next year', 'next month', 'next season', 'next quarter',
            'rally', 'crash', 'surge', 'plunge', 'reach', 'hit',
            'target', 'outlook', 'projection', 'bet', 'wager',
            'bullish', 'bearish', 'bottom', 'peak', 'high', 'low',
            # Sports
            'will win', 'will lose', 'championship', 'playoffs', 'super bowl',
            'world series', 'finals', 'mvp', 'season prediction', 'odds',
            'favored', 'underdog', 'spread', 'over under',
            # Politics
            'will pass', 'will fail', 'election', 'poll', 'vote',
            'majority', 'minority', 'swing state', 'electoral',
            'campaign promise', 'policy will', 'legislation will',
            # Entertainment
            'box office', 'opening weekend', 'will gross', 'blockbuster',
            'oscar', 'emmy', 'grammy', 'nomination', 'award season',
            'streaming numbers', 'ratings will', 'viewership',
            # Science/Health/Climate
            'study predicts', 'research shows', 'scientists predict',
            'climate projection', 'temperature will', 'sea level',
            'pandemic', 'outbreak', 'vaccine', 'trial results',
            # General
            'i believe', 'mark my words', 'calling it now', 'guaranteed'
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
