# services/auto_agent.py
"""
Auto-Agent Pipeline
Orchestrates: RSS Ingestion → AI Extraction → Polymarket Matching → Database Storage
"""
import os
import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid

from anthropic import Anthropic
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import Pundit, Prediction, Match, Position, PunditMetrics, RawContent
from services.rss_ingestion import RSSIngestionService, NewsArticle, KNOWN_PUNDITS
from services.polymarket import MarketMatcher, PolymarketService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


EXTRACTION_PROMPT = """
You are analyzing a news article to extract specific predictions about future events made by notable individuals.

Article Title: {title}
Source: {source}
Date: {date}

Article Text:
---
{text}
---

IMPORTANT: Extract predictions from ANY notable person mentioned in the article - politicians, CEOs, analysts, experts, celebrities, athletes, commentators, etc. 
Do NOT limit to a predefined list. If someone notable makes a prediction, capture it.

A prediction must:
1. Be attributed to a specific NAMED person (full name required)
2. Make a claim about something that will/won't happen in the future
3. Be specific enough to potentially verify later
4. Have a timeframe (explicit or implicit)

The person must be notable - someone with a public profile:
- Politicians, government officials
- CEOs, executives, investors
- Analysts, economists, experts
- TV personalities, journalists
- Athletes, coaches, sports commentators
- Religious leaders, activists
- Scientists, researchers
- Celebrities with influence

For each prediction found, extract:
- pundit_name: Full name of the person (e.g., "Elon Musk", not "Musk" or "Tesla CEO")
- pundit_title: Their role/title (e.g., "Tesla CEO", "Senator", "CNBC Host")
- pundit_affiliation: Organization they're associated with
- claim: The specific prediction (phrased as a statement)
- confidence: The speaker's implied confidence (certain/high/medium/low/speculative)
- timeframe: When this will be verifiable (date like "2026-12-31", or "within 6 months", etc.)
- quote: The exact quote from the article (verbatim)
- category: politics/economy/markets/crypto/tech/macro/sports/entertainment/religion/science/business/media/health/climate/geopolitics/us/uk/eu/china/japan/india/israel/russia/brazil/latam/middle-east/africa/asia-pacific

Return ONLY valid JSON array:
[
  {{
    "pundit_name": "Janet Yellen",
    "pundit_title": "Treasury Secretary",
    "pundit_affiliation": "US Treasury Department",
    "claim": "US economy will achieve soft landing in 2026",
    "confidence": "high",
    "timeframe": "2026-12-31",
    "quote": "We expect the economy to continue its path to a soft landing",
    "category": "economy"
  }}
]

If no predictions are found, return empty array: []
"""


class AutoAgentPipeline:
    """
    Complete pipeline for automatic prediction extraction and tracking
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.rss_service = RSSIngestionService()
        self.market_matcher = None  # Initialized lazily for async
        self.anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        # Cache pundits
        self.pundits_cache: Dict[str, Pundit] = {}
        
    async def initialize(self):
        """Initialize async components"""
        self.market_matcher = MarketMatcher()
        await self._load_pundits_cache()
    
    async def _load_pundits_cache(self):
        """Load pundits into memory for quick lookup (limited for performance)"""
        try:
            # Limit to 500 pundits to prevent memory issues
            result = self.db.execute(select(Pundit).limit(500))
            pundits = result.scalars().all()
            
            for pundit in pundits:
                # Cache by name and username
                self.pundits_cache[pundit.name.lower()] = pundit
                if pundit.username:
                    self.pundits_cache[pundit.username.lower()] = pundit
            
            logger.info(f"Loaded {len(self.pundits_cache)} pundits into cache")
        except Exception as e:
            logger.error(f"Failed to load pundits cache: {e}")
            # Continue with empty cache - will just create new pundits as needed
    
    def _find_pundit(self, name: str) -> Optional[Pundit]:
        """Find a pundit by name (fuzzy matching)"""
        name_lower = name.lower()
        
        # Direct match
        if name_lower in self.pundits_cache:
            return self.pundits_cache[name_lower]
        
        # Partial match
        for cached_name, pundit in self.pundits_cache.items():
            if name_lower in cached_name or cached_name in name_lower:
                return pundit
        
        return None
    
    def _create_username(self, name: str) -> str:
        """Generate a username from a name"""
        # Remove special chars and create lowercase username
        import re
        username = re.sub(r'[^a-zA-Z0-9\s]', '', name)
        username = username.lower().replace(' ', '_')
        return username[:50]  # Limit length
    
    def _auto_create_pundit(self, name: str, title: str = "", affiliation: str = "", category: str = "general") -> Pundit:
        """Auto-create a new pundit when discovered"""
        username = self._create_username(name)
        
        # Check if username already exists (might have different name variation)
        existing = self.db.execute(
            select(Pundit).where(Pundit.username == username)
        ).scalar_one_or_none()
        
        if existing:
            # Add to cache and return existing
            self.pundits_cache[name.lower()] = existing
            return existing
        
        # Determine domains from category
        category_to_domains = {
            "politics": ["politics"],
            "economy": ["economy"],
            "markets": ["markets"],
            "crypto": ["crypto"],
            "tech": ["tech"],
            "sports": ["sports"],
            "entertainment": ["entertainment"],
            "religion": ["religion"],
            "science": ["science"],
            "health": ["health"],
            "climate": ["climate"],
            "geopolitics": ["geopolitics", "politics"],
            "us": ["politics", "us"],
            "uk": ["politics", "uk"],
            "eu": ["politics", "eu"],
        }
        domains = category_to_domains.get(category.lower(), ["general"])
        
        # Create new pundit
        pundit = Pundit(
            id=uuid.uuid4(),
            name=name,
            username=username,
            affiliation=affiliation or title,
            bio=f"{title}. Auto-discovered by TrackRecord bot." if title else "Auto-discovered by TrackRecord bot.",
            domains=domains,
            verified=False,  # Auto-discovered pundits start unverified
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(pundit)
        
        # Create initial metrics
        metrics = PunditMetrics(
            pundit_id=pundit.id,
            total_predictions=0,
            resolved_predictions=0,
            paper_total_pnl=0.0,
            paper_win_rate=0.0,
            paper_roi=0.0
        )
        self.db.add(metrics)
        
        # Add to cache
        self.pundits_cache[name.lower()] = pundit
        self.pundits_cache[username.lower()] = pundit
        
        logger.info(f"Auto-created new pundit: {name} (@{username}) - {affiliation}")
        
        return pundit
    
    async def run_pipeline(self, feed_keys: Optional[List[str]] = None, max_articles: int = 50) -> Dict:
        """
        Run the complete pipeline:
        1. Fetch RSS articles
        2. Filter for prediction content
        3. Extract predictions using AI
        4. Match to Polymarket
        5. Store in database
        
        Args:
            feed_keys: Optional list of specific feeds to process
            max_articles: Maximum articles to process per run (default 50)
        """
        stats = {
            "articles_fetched": 0,
            "articles_with_predictions": 0,
            "predictions_extracted": 0,
            "predictions_matched": 0,
            "predictions_stored": 0,
            "new_pundits_created": 0,
            "errors": []
        }
        
        logger.info(f"Starting auto-agent pipeline (max {max_articles} articles)...")
        
        # Step 1: Fetch RSS articles
        if feed_keys:
            articles = []
            for key in feed_keys:
                articles.extend(self.rss_service.fetch_feed(key))
        else:
            articles = self.rss_service.fetch_all_feeds()
        
        stats["articles_fetched"] = len(articles)
        logger.info(f"Fetched {len(articles)} articles from RSS feeds")
        
        # Step 2: Filter for prediction-like content
        prediction_articles = self.rss_service.filter_prediction_articles(articles)
        
        # Limit to max_articles to prevent long-running jobs
        if len(prediction_articles) > max_articles:
            prediction_articles = prediction_articles[:max_articles]
            logger.info(f"Limiting to {max_articles} articles (from {len(articles)} fetched)")
        
        logger.info(f"Processing {len(prediction_articles)} articles with prediction keywords")
        
        # Step 3-5: Process each article
        for article in prediction_articles:
            try:
                result = await self._process_article(article)
                
                if result["predictions_found"] > 0:
                    stats["articles_with_predictions"] += 1
                    stats["predictions_extracted"] += result["predictions_found"]
                    stats["predictions_matched"] += result["predictions_matched"]
                    stats["predictions_stored"] += result["predictions_stored"]
                    stats["new_pundits_created"] += result.get("new_pundits", 0)
                    
            except Exception as e:
                logger.error(f"Error processing article: {e}")
                stats["errors"].append(str(e))
        
        logger.info(f"Pipeline complete. Stats: {stats}")
        return stats
    
    async def _process_article(self, article: NewsArticle) -> Dict:
        """Process a single article through the pipeline"""
        result = {
            "predictions_found": 0,
            "predictions_matched": 0,
            "predictions_stored": 0,
            "new_pundits": 0
        }
        
        # Check for duplicate by URL hash
        url_hash = hashlib.sha256(article.url.encode()).hexdigest()
        existing = self.db.execute(
            select(RawContent).where(RawContent.content_hash == url_hash)
        ).scalar_one_or_none()
        
        if existing:
            logger.debug(f"Skipping duplicate article: {article.title}")
            return result
        
        # Extract predictions using AI (now extracts from ANY notable person)
        predictions_data = await self._extract_predictions(article)
        result["predictions_found"] = len(predictions_data)
        
        if not predictions_data:
            return result
        
        # Process each extracted prediction
        for pred_data in predictions_data:
            try:
                pundit_name = pred_data.get("pundit_name", "").strip()
                if not pundit_name or len(pundit_name) < 3:
                    continue
                
                # Find existing pundit or auto-create new one
                pundit = self._find_pundit(pundit_name)
                is_new_pundit = False
                if not pundit:
                    # Auto-create new pundit!
                    pundit = self._auto_create_pundit(
                        name=pundit_name,
                        title=pred_data.get("pundit_title", ""),
                        affiliation=pred_data.get("pundit_affiliation", ""),
                        category=pred_data.get("category", "general")
                    )
                    is_new_pundit = True
                    result["new_pundits"] += 1
                
                # Create prediction
                prediction = await self._create_prediction(pundit, pred_data, article)
                if not prediction:
                    continue
                
                # Match to Polymarket
                match_result = await self._match_to_polymarket(prediction)
                if match_result:
                    result["predictions_matched"] += 1
                
                # Save to database
                self.db.add(prediction)
                result["predictions_stored"] += 1
                
            except Exception as e:
                logger.error(f"Error processing prediction: {e}")
        
        # Commit all changes
        self.db.commit()
        
        return result
    
    async def _extract_predictions(self, article: NewsArticle) -> List[Dict]:
        """Use Claude to extract predictions from article - finds ANY notable person"""
        prompt = EXTRACTION_PROMPT.format(
            title=article.title,
            source=article.source,
            date=article.published.isoformat(),
            text=f"{article.title}\n\n{article.summary}"
        )
        
        try:
            response = self.anthropic.messages.create(
                model="claude-3-haiku-20240307",  # Use Haiku for speed/cost
                max_tokens=2000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            import json
            content = response.content[0].text
            
            # Handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content.strip())
            
        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            return []
    
    async def _create_prediction(
        self, 
        pundit: Pundit, 
        pred_data: Dict, 
        article: NewsArticle
    ) -> Optional[Prediction]:
        """Create a Prediction object from extracted data"""
        
        # Parse timeframe
        timeframe = self._parse_timeframe(pred_data.get("timeframe", ""))
        
        # Map confidence
        confidence_map = {
            'certain': 0.95, 'high': 0.80, 'medium': 0.60,
            'low': 0.40, 'speculative': 0.25
        }
        confidence = confidence_map.get(
            pred_data.get("confidence", "medium").lower(), 
            0.60
        )
        
        # Create content hash for deduplication
        content_hash = hashlib.sha256(
            f"{pundit.id}|{pred_data['claim']}|{article.url}".encode()
        ).hexdigest()
        
        # Check for duplicate
        existing = self.db.execute(
            select(Prediction).where(Prediction.content_hash == content_hash)
        ).scalar_one_or_none()
        
        if existing:
            return None
        
        return Prediction(
            id=uuid.uuid4(),
            pundit_id=pundit.id,
            claim=pred_data["claim"],
            confidence=confidence,
            timeframe=timeframe,
            quote=pred_data.get("quote", pred_data["claim"]),
            category=pred_data.get("category", "general"),
            source_url=article.url,
            source_type="rss",
            captured_at=datetime.utcnow(),
            content_hash=content_hash,
            status="pending",
            flagged=False,
            created_at=datetime.utcnow()
        )
    
    async def _match_to_polymarket(self, prediction: Prediction) -> Optional[Match]:
        """Find and create a Polymarket match for a prediction"""
        if not self.market_matcher:
            return None
        
        try:
            matches = await self.market_matcher.find_matching_markets(
                prediction.claim,
                prediction.category,
                top_k=3
            )
            
            if not matches:
                return None
            
            best_match = matches[0]
            
            # Only auto-match if confidence is high
            if best_match["similarity_score"] < 0.3:
                # Add to review queue instead
                prediction.status = "needs_review"
                return None
            
            # Create match
            match = Match(
                id=uuid.uuid4(),
                prediction_id=prediction.id,
                market_id=best_match["market_id"],
                market_slug=best_match.get("market_slug"),
                market_question=best_match["market_question"],
                market_end_date=datetime.fromisoformat(best_match["market_end_date"]) if best_match.get("market_end_date") else None,
                similarity_score=best_match["similarity_score"],
                match_type="auto" if best_match["similarity_score"] > 0.6 else "suggested",
                entry_price=best_match["current_yes_price"],
                entry_timestamp=datetime.utcnow(),
                matched_at=datetime.utcnow()
            )
            
            self.db.add(match)
            prediction.status = "matched"
            prediction.matched_at = datetime.utcnow()
            
            # Create paper trading position
            await self._create_position(prediction, match)
            
            return match
            
        except Exception as e:
            logger.error(f"Polymarket matching failed: {e}")
            return None
    
    async def _create_position(self, prediction: Prediction, match: Match):
        """Create a paper trading position"""
        # Position size based on confidence
        size_map = {0.95: 1000, 0.80: 500, 0.60: 300, 0.40: 100, 0.25: 50}
        position_size = size_map.get(prediction.confidence, 300)
        
        shares = position_size / match.entry_price if match.entry_price > 0 else 0
        
        position = Position(
            id=uuid.uuid4(),
            prediction_id=prediction.id,
            match_id=match.id,
            pundit_id=prediction.pundit_id,
            market_id=match.market_id,
            market_question=match.market_question,
            entry_price=match.entry_price,
            entry_timestamp=datetime.utcnow(),
            position_size=position_size,
            shares=shares,
            status="open",
            last_updated=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        self.db.add(position)
    
    def _parse_timeframe(self, timeframe_str: str) -> datetime:
        """Parse timeframe string into datetime"""
        import re
        
        # Try ISO date format first
        try:
            return datetime.fromisoformat(timeframe_str)
        except:
            pass
        
        # Try common patterns
        timeframe_lower = timeframe_str.lower()
        
        if "month" in timeframe_lower:
            match = re.search(r'(\d+)', timeframe_str)
            months = int(match.group(1)) if match else 6
            return datetime.utcnow() + timedelta(days=30 * months)
        
        if "year" in timeframe_lower:
            match = re.search(r'(\d+)', timeframe_str)
            years = int(match.group(1)) if match else 1
            return datetime.utcnow() + timedelta(days=365 * years)
        
        if "week" in timeframe_lower:
            match = re.search(r'(\d+)', timeframe_str)
            weeks = int(match.group(1)) if match else 4
            return datetime.utcnow() + timedelta(weeks=weeks)
        
        if "day" in timeframe_lower:
            match = re.search(r'(\d+)', timeframe_str)
            days = int(match.group(1)) if match else 30
            return datetime.utcnow() + timedelta(days=days)
        
        # Look for year mentions like "2026", "end of 2025"
        year_match = re.search(r'20\d{2}', timeframe_str)
        if year_match:
            year = int(year_match.group())
            return datetime(year, 12, 31)
        
        # Default: 6 months from now
        return datetime.utcnow() + timedelta(days=180)
    
    async def close(self):
        """Cleanup resources"""
        if self.market_matcher:
            await self.market_matcher.close()


# Standalone test/run function
async def run_auto_agent():
    """Run the auto-agent pipeline"""
    from database.session import SessionLocal
    
    db = SessionLocal()
    
    try:
        pipeline = AutoAgentPipeline(db)
        await pipeline.initialize()
        
        stats = await pipeline.run_pipeline()
        
        print("\n" + "="*60)
        print("AUTO-AGENT PIPELINE RESULTS")
        print("="*60)
        print(f"Articles fetched: {stats['articles_fetched']}")
        print(f"Articles with predictions: {stats['articles_with_predictions']}")
        print(f"Predictions extracted: {stats['predictions_extracted']}")
        print(f"Predictions matched to Polymarket: {stats['predictions_matched']}")
        print(f"Predictions stored: {stats['predictions_stored']}")
        
        if stats['errors']:
            print(f"\nErrors: {len(stats['errors'])}")
            for err in stats['errors'][:5]:
                print(f"  - {err}")
        
        await pipeline.close()
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(run_auto_agent())
