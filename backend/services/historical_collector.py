# services/historical_collector.py
"""
Historical Data Collector Service
Collects prediction data from 2020-present using multiple sources:
- GDELT Project (free news database)
- Google News RSS with date filters
- News API archives
"""
import os
import asyncio
import httpx
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import feedparser
from urllib.parse import quote_plus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pundits to search for - focusing on most trackable ones
HISTORICAL_PUNDITS = {
    # Finance
    "Jim Cramer": ["markets", "economy"],
    "Cathie Wood": ["markets", "tech", "crypto"],
    "Peter Schiff": ["markets", "crypto", "economy"],
    "Michael Saylor": ["crypto"],
    "Elon Musk": ["tech", "crypto", "markets"],
    "Ray Dalio": ["markets", "economy"],
    "Bill Ackman": ["markets"],
    "Paul Krugman": ["economy"],
    "Larry Summers": ["economy"],
    "Nouriel Roubini": ["economy", "crypto"],
    "Robert Kiyosaki": ["markets", "crypto"],
    "Tom Lee": ["markets", "crypto"],
    
    # Politics
    "Donald Trump": ["politics", "economy", "us"],
    "Joe Biden": ["politics", "economy", "us"],
    "Nancy Pelosi": ["politics", "us"],
    "Bernie Sanders": ["politics", "economy", "us"],
    "Nate Silver": ["politics"],
    
    # Tech
    "Sam Altman": ["tech"],
    "Marc Andreessen": ["tech", "crypto"],
    "Balaji Srinivasan": ["crypto", "tech"],
    
    # International
    "Boris Johnson": ["politics", "uk"],
    "Emmanuel Macron": ["politics", "eu"],
    "Angela Merkel": ["politics", "eu"],
    "Vladimir Putin": ["politics", "russia", "geopolitics"],
    "Xi Jinping": ["politics", "china", "geopolitics"],
    "Narendra Modi": ["politics", "india"],
    "Benjamin Netanyahu": ["politics", "israel", "middle-east"],
    
    # Sports
    "Stephen A. Smith": ["sports"],
    "Skip Bayless": ["sports"],
    "Gary Neville": ["sports", "uk"],
}

# Keywords that indicate predictions
PREDICTION_KEYWORDS = [
    "predicts", "prediction", "forecast", "expects", "will happen",
    "by 2025", "by 2026", "by end of", "within months", "next year",
    "going to", "will reach", "will hit", "will be", "will win",
    "believes", "projects", "anticipates", "warns", "claims"
]


@dataclass
class HistoricalArticle:
    title: str
    url: str
    content: str
    published: datetime
    source: str
    pundit: str
    search_query: str


class HistoricalCollector:
    """Collects historical articles containing predictions from various sources"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.processed_urls: set = set()
        self.collected_articles: List[HistoricalArticle] = []
        
    async def close(self):
        await self.client.aclose()
    
    def _generate_search_queries(self, pundit: str, year: int) -> List[str]:
        """Generate search queries for a pundit and year"""
        queries = []
        # Basic prediction queries
        queries.append(f'"{pundit}" prediction {year}')
        queries.append(f'"{pundit}" predicts {year}')
        queries.append(f'"{pundit}" forecast {year}')
        queries.append(f'"{pundit}" expects {year}')
        queries.append(f'"{pundit}" warns {year}')
        queries.append(f'"{pundit}" claims {year}')
        return queries
    
    async def search_google_news_rss(
        self, 
        query: str, 
        after_date: datetime,
        before_date: datetime
    ) -> List[Dict]:
        """Search Google News RSS with date filters"""
        articles = []
        
        # Format dates for Google News
        after_str = after_date.strftime("%Y-%m-%d")
        before_str = before_date.strftime("%Y-%m-%d")
        
        # Google News RSS search URL with date filter
        encoded_query = quote_plus(f'{query} after:{after_str} before:{before_str}')
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                feed = feedparser.parse(response.text)
                for entry in feed.entries[:10]:  # Limit per query
                    if entry.link not in self.processed_urls:
                        self.processed_urls.add(entry.link)
                        articles.append({
                            "title": entry.get("title", ""),
                            "url": entry.link,
                            "summary": entry.get("summary", ""),
                            "published": entry.get("published", ""),
                            "source": "Google News"
                        })
        except Exception as e:
            logger.error(f"Error searching Google News: {e}")
        
        return articles
    
    async def search_gdelt(
        self,
        query: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Search GDELT Project for historical articles"""
        articles = []
        
        # GDELT DOC API - free access to news articles
        start_str = start_date.strftime("%Y%m%d%H%M%S")
        end_str = end_date.strftime("%Y%m%d%H%M%S")
        
        encoded_query = quote_plus(query)
        url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={encoded_query}&mode=artlist&maxrecords=25&startdatetime={start_str}&enddatetime={end_str}&format=json"
        
        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                for article in data.get("articles", []):
                    article_url = article.get("url", "")
                    if article_url and article_url not in self.processed_urls:
                        self.processed_urls.add(article_url)
                        
                        # Parse date
                        date_str = article.get("seendate", "")
                        try:
                            pub_date = datetime.strptime(date_str[:14], "%Y%m%d%H%M%S")
                        except:
                            pub_date = datetime.now()
                        
                        articles.append({
                            "title": article.get("title", ""),
                            "url": article_url,
                            "summary": article.get("title", ""),  # GDELT doesn't provide summary
                            "published": pub_date.isoformat(),
                            "source": article.get("domain", "GDELT"),
                            "language": article.get("language", "English")
                        })
        except Exception as e:
            logger.error(f"Error searching GDELT: {e}")
        
        return articles
    
    async def fetch_article_content(self, url: str) -> Optional[str]:
        """Fetch full article content from URL"""
        try:
            response = await self.client.get(url, follow_redirects=True)
            if response.status_code == 200:
                # Basic text extraction - in production use newspaper3k or similar
                from html.parser import HTMLParser
                
                class TextExtractor(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.text = []
                        self.skip = False
                        
                    def handle_starttag(self, tag, attrs):
                        if tag in ['script', 'style', 'nav', 'header', 'footer']:
                            self.skip = True
                            
                    def handle_endtag(self, tag):
                        if tag in ['script', 'style', 'nav', 'header', 'footer']:
                            self.skip = False
                            
                    def handle_data(self, data):
                        if not self.skip:
                            text = data.strip()
                            if len(text) > 20:  # Skip short fragments
                                self.text.append(text)
                
                parser = TextExtractor()
                parser.feed(response.text)
                content = " ".join(parser.text)
                
                # Limit content length
                return content[:10000] if len(content) > 10000 else content
        except Exception as e:
            logger.debug(f"Error fetching article {url}: {e}")
        
        return None
    
    async def collect_for_pundit(
        self,
        pundit: str,
        categories: List[str],
        start_date: datetime,
        end_date: datetime,
        max_articles: int = 20
    ) -> List[HistoricalArticle]:
        """Collect historical articles for a specific pundit"""
        articles = []
        
        # Generate date ranges (quarterly to avoid too many results)
        current_date = start_date
        while current_date < end_date and len(articles) < max_articles:
            quarter_end = min(current_date + timedelta(days=90), end_date)
            
            # Generate queries
            year = current_date.year
            queries = self._generate_search_queries(pundit, year)
            
            for query in queries[:3]:  # Limit queries per time period
                if len(articles) >= max_articles:
                    break
                    
                # Search Google News
                google_results = await self.search_google_news_rss(
                    query, current_date, quarter_end
                )
                
                # Search GDELT
                gdelt_results = await self.search_gdelt(
                    f'"{pundit}" prediction',
                    current_date,
                    quarter_end
                )
                
                # Combine and process
                all_results = google_results + gdelt_results
                
                for result in all_results[:5]:  # Limit per query
                    if len(articles) >= max_articles:
                        break
                    
                    # Check if article likely contains prediction
                    title = result.get("title", "").lower()
                    if any(kw in title for kw in PREDICTION_KEYWORDS) or pundit.lower() in title:
                        # Fetch content
                        content = await self.fetch_article_content(result["url"])
                        if content and pundit.lower() in content.lower():
                            try:
                                pub_date = datetime.fromisoformat(result["published"].replace("Z", ""))
                            except:
                                pub_date = current_date
                            
                            articles.append(HistoricalArticle(
                                title=result["title"],
                                url=result["url"],
                                content=content,
                                published=pub_date,
                                source=result["source"],
                                pundit=pundit,
                                search_query=query
                            ))
                            logger.info(f"Found article for {pundit}: {result['title'][:50]}...")
                
                # Rate limiting
                await asyncio.sleep(1)
            
            current_date = quarter_end
        
        return articles
    
    async def collect_all(
        self,
        start_year: int = 2020,
        end_year: int = None,
        pundits: Dict[str, List[str]] = None,
        max_per_pundit: int = 15
    ) -> List[HistoricalArticle]:
        """Collect historical articles for all pundits"""
        if end_year is None:
            end_year = datetime.now().year
        
        if pundits is None:
            pundits = HISTORICAL_PUNDITS
        
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31)
        
        all_articles = []
        
        for pundit, categories in pundits.items():
            logger.info(f"Collecting historical data for {pundit}...")
            
            articles = await self.collect_for_pundit(
                pundit=pundit,
                categories=categories,
                start_date=start_date,
                end_date=end_date,
                max_articles=max_per_pundit
            )
            
            all_articles.extend(articles)
            logger.info(f"Found {len(articles)} articles for {pundit}")
            
            # Rate limiting between pundits
            await asyncio.sleep(2)
        
        self.collected_articles = all_articles
        return all_articles
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about collected articles"""
        stats = {
            "total_articles": len(self.collected_articles),
            "by_pundit": {},
            "by_year": {},
            "unique_sources": set()
        }
        
        for article in self.collected_articles:
            # By pundit
            if article.pundit not in stats["by_pundit"]:
                stats["by_pundit"][article.pundit] = 0
            stats["by_pundit"][article.pundit] += 1
            
            # By year
            year = article.published.year
            if year not in stats["by_year"]:
                stats["by_year"][year] = 0
            stats["by_year"][year] += 1
            
            # Sources
            stats["unique_sources"].add(article.source)
        
        stats["unique_sources"] = list(stats["unique_sources"])
        return stats


class HistoricalPipeline:
    """
    Complete pipeline for historical data collection and processing
    """
    
    def __init__(self, db_session):
        self.db = db_session
        self.collector = HistoricalCollector()
        
    async def run(
        self,
        start_year: int = 2020,
        max_per_pundit: int = 15,
        auto_process: bool = True
    ) -> Dict:
        """
        Run the historical collection pipeline
        
        Args:
            start_year: Start collecting from this year
            max_per_pundit: Maximum articles to collect per pundit
            auto_process: If True, automatically extract predictions
        """
        from services.auto_agent import AutoAgentPipeline
        from services.rss_ingestion import NewsArticle
        
        results = {
            "status": "running",
            "articles_collected": 0,
            "predictions_extracted": 0,
            "errors": []
        }
        
        try:
            # Step 1: Collect historical articles
            logger.info(f"Starting historical collection from {start_year}...")
            articles = await self.collector.collect_all(
                start_year=start_year,
                max_per_pundit=max_per_pundit
            )
            
            results["articles_collected"] = len(articles)
            results["collection_stats"] = self.collector.get_collection_stats()
            
            logger.info(f"Collected {len(articles)} historical articles")
            
            # Step 2: Process with AI if enabled
            if auto_process and articles:
                logger.info("Processing articles with AI extraction...")
                
                pipeline = AutoAgentPipeline(self.db)
                
                for article in articles:
                    try:
                        # Convert to NewsArticle format
                        news_article = NewsArticle(
                            title=article.title,
                            url=article.url,
                            summary=article.content[:2000],  # Use content as summary
                            published=article.published,
                            source=article.source
                        )
                        
                        # Extract predictions
                        predictions = await pipeline.extract_predictions_from_article(
                            news_article, 
                            article.content
                        )
                        
                        if predictions:
                            results["predictions_extracted"] += len(predictions)
                            logger.info(f"Extracted {len(predictions)} predictions from: {article.title[:50]}...")
                        
                        # Rate limiting for AI calls
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        results["errors"].append(f"Error processing {article.url}: {str(e)}")
                        logger.error(f"Error processing article: {e}")
            
            results["status"] = "completed"
            
        except Exception as e:
            results["status"] = "failed"
            results["errors"].append(str(e))
            logger.error(f"Pipeline failed: {e}")
        
        finally:
            await self.collector.close()
        
        return results


# Standalone runner for testing
async def main():
    """Test the historical collector"""
    collector = HistoricalCollector()
    
    try:
        # Test with a few pundits
        test_pundits = {
            "Elon Musk": ["tech", "crypto"],
            "Jim Cramer": ["markets"],
        }
        
        articles = await collector.collect_all(
            start_year=2023,  # Just test recent data
            pundits=test_pundits,
            max_per_pundit=5
        )
        
        print(f"\nCollected {len(articles)} articles:")
        for article in articles:
            print(f"  - {article.pundit}: {article.title[:60]}...")
        
        print(f"\nStats: {collector.get_collection_stats()}")
        
    finally:
        await collector.close()


if __name__ == "__main__":
    asyncio.run(main())
