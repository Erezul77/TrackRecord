# services/scheduler.py
"""
Background Scheduler Service - Non-blocking version
Runs automated tasks in separate threads to avoid blocking the API:
- Historical data collection
- RSS feed ingestion
- Prediction extraction
- Auto-resolution of predictions
- X (Twitter) collection
"""
import os
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread pool for running async tasks - isolated from main API
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="scheduler_")

# Flag to track if we should delay first run
_first_run_delayed = False


def run_async_in_thread(coro):
    """Run an async coroutine in a new event loop in a separate thread"""
    def wrapper():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    return wrapper


class TrackRecordScheduler:
    """
    Manages all scheduled background tasks for TrackRecord
    Uses BackgroundScheduler to run in separate threads (non-blocking)
    """
    
    def __init__(self):
        # Use BackgroundScheduler instead of AsyncIOScheduler
        # This runs jobs in separate threads, not blocking the main API
        self.scheduler = BackgroundScheduler(
            job_defaults={
                'coalesce': True,  # Combine missed runs
                'max_instances': 1,  # Only one instance per job
                'misfire_grace_time': 3600  # 1 hour grace for missed jobs
            }
        )
        self.is_running = False
        self.last_run_times = {}
        self.run_stats = {
            "rss_ingestion": {"runs": 0, "predictions": 0, "errors": 0},
            "historical_collection": {"runs": 0, "articles": 0, "predictions": 0, "errors": 0},
            "auto_resolution": {"runs": 0, "resolved": 0, "flagged": 0, "errors": 0},
            "twitter_collection": {"runs": 0, "tweets": 0, "predictions": 0, "errors": 0}
        }
        self._lock = threading.Lock()
    
    def _run_rss_ingestion_sync(self):
        """Sync wrapper for RSS ingestion - runs in completely isolated thread"""
        import time
        global _first_run_delayed
        
        # Add delay on first run to let API fully start
        if not _first_run_delayed:
            logger.info("First RSS run - waiting 60 seconds for API to stabilize...")
            time.sleep(60)
            _first_run_delayed = True
        
        async def _run():
            # Import fresh to avoid module-level issues
            from database.session import async_session
            from services.auto_agent import AutoAgentPipeline
            
            logger.info("Starting scheduled RSS ingestion (isolated thread)...")
            
            try:
                # Create completely fresh session
                async with async_session() as session:
                    pipeline = AutoAgentPipeline(session)
                    # Shorter timeout - fail fast
                    results = await asyncio.wait_for(
                        pipeline.run_pipeline(max_articles=10),  # Limit articles per run
                        timeout=180  # 3 minute timeout
                    )
                    
                    with self._lock:
                        self.last_run_times["rss_ingestion"] = datetime.now()
                        self.run_stats["rss_ingestion"]["runs"] += 1
                        self.run_stats["rss_ingestion"]["predictions"] += results.get("new_predictions", 0)
                    
                    logger.info(f"RSS ingestion complete: {results}")
                    return results
                    
            except asyncio.TimeoutError:
                logger.error("RSS ingestion timed out after 3 minutes")
                with self._lock:
                    self.run_stats["rss_ingestion"]["errors"] += 1
                return {"error": "timeout"}
            except Exception as e:
                logger.error(f"RSS ingestion failed: {e}")
                with self._lock:
                    self.run_stats["rss_ingestion"]["errors"] += 1
                return {"error": str(e)}
        
        # Run async code in completely new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_run())
        except Exception as e:
            logger.error(f"RSS ingestion thread error: {e}")
            return {"error": str(e)}
        finally:
            try:
                loop.close()
            except:
                pass
    
    def _run_historical_collection_sync(self, start_year: int = 2020, max_per_pundit: int = 10):
        """Sync wrapper for historical collection - runs in background thread"""
        async def _run():
            from database.session import async_session
            from services.historical_collector import HistoricalPipeline
            
            logger.info(f"Starting historical collection from {start_year} (background thread)...")
            
            try:
                async with async_session() as session:
                    pipeline = HistoricalPipeline(session)
                    results = await asyncio.wait_for(
                        pipeline.run(
                            start_year=start_year,
                            max_per_pundit=max_per_pundit,
                            auto_process=True
                        ),
                        timeout=600  # 10 minute timeout
                    )
                    
                    with self._lock:
                        self.last_run_times["historical_collection"] = datetime.now()
                        self.run_stats["historical_collection"]["runs"] += 1
                        self.run_stats["historical_collection"]["articles"] += results.get("articles_collected", 0)
                        self.run_stats["historical_collection"]["predictions"] += results.get("predictions_extracted", 0)
                    
                    logger.info(f"Historical collection complete: {results}")
                    return results
                    
            except asyncio.TimeoutError:
                logger.error("Historical collection timed out after 10 minutes")
                with self._lock:
                    self.run_stats["historical_collection"]["errors"] += 1
                return {"error": "timeout"}
            except Exception as e:
                logger.error(f"Historical collection failed: {e}")
                with self._lock:
                    self.run_stats["historical_collection"]["errors"] += 1
                return {"error": str(e)}
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_run())
        finally:
            loop.close()
    
    def _run_auto_resolution_sync(self):
        """Sync wrapper for auto-resolution - runs in background thread"""
        async def _run():
            from database.session import async_session
            from services.auto_resolver import run_auto_resolution, get_resolver
            
            logger.info("Starting auto-resolution cycle (background thread)...")
            
            try:
                async with async_session() as session:
                    # Step 1: Run standard auto-resolution (market + timeframe based)
                    results = await asyncio.wait_for(
                        run_auto_resolution(session),
                        timeout=120  # 2 minute timeout
                    )
                    
                    standard_resolved = results.get("market_resolved", 0) + results.get("expired_auto_resolved", 0)
                    
                    # Step 2: Run AI resolution on remaining expired predictions
                    # Run lighter to avoid overwhelming the server
                    ai_resolved = 0
                    try:
                        resolver = get_resolver()
                        ai_results = await asyncio.wait_for(
                            resolver.ai_resolve_batch(session, limit=5),  # Resolve up to 5 per cycle (lighter load)
                            timeout=120  # 2 minute timeout for AI
                        )
                        ai_resolved = ai_results.get("resolved_yes", 0) + ai_results.get("resolved_no", 0)
                        logger.info(f"AI resolution complete: {ai_resolved} resolved")
                    except asyncio.TimeoutError:
                        logger.warning("AI resolution timed out - will retry next cycle")
                    except Exception as e:
                        logger.error(f"AI resolution error: {e}")
                    
                    with self._lock:
                        self.last_run_times["auto_resolution"] = datetime.now()
                        self.run_stats["auto_resolution"]["runs"] += 1
                        self.run_stats["auto_resolution"]["resolved"] += standard_resolved + ai_resolved
                        self.run_stats["auto_resolution"]["flagged"] += results.get("flagged_for_review", 0)
                    
                    logger.info(f"Auto-resolution complete: {standard_resolved} standard + {ai_resolved} AI resolved")
                    return {**results, "ai_resolved": ai_resolved}
                    
            except asyncio.TimeoutError:
                logger.error("Auto-resolution timed out after 2 minutes")
                with self._lock:
                    self.run_stats["auto_resolution"]["errors"] += 1
                return {"error": "timeout"}
            except Exception as e:
                logger.error(f"Auto-resolution failed: {e}")
                with self._lock:
                    self.run_stats["auto_resolution"]["errors"] += 1
                return {"error": str(e)}
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_run())
        finally:
            loop.close()
    
    def _run_twitter_collection_sync(self, max_pundits: int = 20):
        """Sync wrapper for Twitter collection - runs in background thread"""
        async def _run():
            # Check if Twitter is configured
            if not os.getenv("TWITTER_BEARER_TOKEN"):
                logger.warning("Twitter collection skipped - no bearer token configured")
                return {"skipped": True, "reason": "No Twitter token"}
            
            from database.session import async_session
            from services.twitter_ingestion import TwitterPredictionCollector, get_twitter_pundits
            from services.prediction_extractor import PredictionExtractor
            from database.models import Prediction, Pundit
            from sqlalchemy import select
            import hashlib
            
            logger.info("Starting Twitter prediction collection (background thread)...")
            
            try:
                async with async_session() as session:
                    collector = TwitterPredictionCollector()
                    extractor = PredictionExtractor()
                    
                    # Get tracked pundits with Twitter handles
                    usernames = get_twitter_pundits()[:max_pundits]
                    
                    # Collect tweets from last 24 hours with timeout
                    results = await asyncio.wait_for(
                        collector.collect_from_multiple_pundits(usernames, since_hours=24),
                        timeout=180  # 3 minute timeout
                    )
                    await collector.close()
                    
                    total_tweets = sum(len(tweets) for tweets in results.values())
                    new_predictions = 0
                    
                    for username, tweets in results.items():
                        for tweet in tweets:
                            try:
                                content_hash = hashlib.sha256(tweet.url.encode()).hexdigest()
                                
                                # Skip duplicates
                                existing = await session.execute(
                                    select(Prediction).where(Prediction.content_hash == content_hash)
                                )
                                if existing.scalar_one_or_none():
                                    continue
                                
                                # Find pundit
                                pundit_result = await session.execute(
                                    select(Pundit).where(Pundit.username == username)
                                )
                                pundit = pundit_result.scalar_one_or_none()
                                
                                if not pundit:
                                    pundit = Pundit(
                                        name=tweet.author_name,
                                        username=username,
                                        bio=f"Twitter: @{username}",
                                        domains=["general"]
                                    )
                                    session.add(pundit)
                                    await session.flush()
                                
                                # Extract prediction with timeout
                                extraction = await asyncio.wait_for(
                                    extractor.extract_from_text(
                                        text=tweet.text,
                                        source_url=tweet.url,
                                        author_name=tweet.author_name
                                    ),
                                    timeout=30  # 30 sec per extraction
                                )
                                
                                if extraction and extraction.get("has_prediction"):
                                    timeframe = datetime.now() + timedelta(days=extraction.get("timeframe_days", 365))
                                    
                                    prediction = Prediction(
                                        pundit_id=pundit.id,
                                        claim=extraction.get("claim", tweet.text[:500]),
                                        quote=tweet.text,
                                        confidence=extraction.get("confidence", 0.5),
                                        category=extraction.get("category", "general"),
                                        timeframe=timeframe,
                                        source_url=tweet.url,
                                        source_type="twitter",
                                        content_hash=content_hash,
                                        captured_at=tweet.created_at,
                                        status="open"
                                    )
                                    session.add(prediction)
                                    new_predictions += 1
                                    
                            except asyncio.TimeoutError:
                                logger.warning(f"Extraction timeout for tweet from {username}")
                            except Exception as e:
                                logger.error(f"Error processing tweet from {username}: {e}")
                    
                    await session.commit()
                    
                    with self._lock:
                        self.last_run_times["twitter_collection"] = datetime.now()
                        self.run_stats["twitter_collection"]["runs"] += 1
                        self.run_stats["twitter_collection"]["tweets"] += total_tweets
                        self.run_stats["twitter_collection"]["predictions"] += new_predictions
                    
                    logger.info(f"Twitter collection complete: {total_tweets} tweets, {new_predictions} new predictions")
                    
                    return {
                        "tweets_found": total_tweets,
                        "new_predictions": new_predictions
                    }
                    
            except asyncio.TimeoutError:
                logger.error("Twitter collection timed out after 3 minutes")
                with self._lock:
                    self.run_stats["twitter_collection"]["errors"] += 1
                return {"error": "timeout"}
            except Exception as e:
                logger.error(f"Twitter collection failed: {e}")
                with self._lock:
                    self.run_stats["twitter_collection"]["errors"] += 1
                return {"error": str(e)}
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_run())
        finally:
            loop.close()
    
    def add_rss_job(self, interval_hours: int = 6):
        """Schedule RSS ingestion job"""
        self.scheduler.add_job(
            self._run_rss_ingestion_sync,
            trigger=IntervalTrigger(hours=interval_hours),
            id="rss_ingestion",
            name="RSS Feed Ingestion",
            replace_existing=True
        )
        logger.info(f"RSS ingestion scheduled every {interval_hours} hours")
    
    def add_historical_job(
        self,
        cron_hour: int = 3,  # Run at 3 AM
        cron_day_of_week: str = "sun",  # Run on Sundays
        start_year: int = 2020
    ):
        """Schedule historical collection job (weekly)"""
        self.scheduler.add_job(
            self._run_historical_collection_sync,
            trigger=CronTrigger(hour=cron_hour, day_of_week=cron_day_of_week),
            id="historical_collection",
            name="Historical Data Collection",
            replace_existing=True,
            kwargs={"start_year": start_year, "max_per_pundit": 10}
        )
        logger.info(f"Historical collection scheduled for {cron_day_of_week} at {cron_hour}:00")
    
    def add_auto_resolution_job(self, interval_hours: int = 4):
        """Schedule auto-resolution job"""
        self.scheduler.add_job(
            self._run_auto_resolution_sync,
            trigger=IntervalTrigger(hours=interval_hours),
            id="auto_resolution",
            name="Auto Resolution",
            replace_existing=True
        )
        logger.info(f"Auto-resolution scheduled every {interval_hours} hours")
    
    def add_twitter_job(self, interval_hours: int = 6):
        """Schedule Twitter collection job"""
        self.scheduler.add_job(
            self._run_twitter_collection_sync,
            trigger=IntervalTrigger(hours=interval_hours),
            id="twitter_collection",
            name="Twitter Collection",
            replace_existing=True
        )
        logger.info(f"Twitter collection scheduled every {interval_hours} hours")
    
    def start(
        self,
        rss_interval_hours: int = 3,  # Run every 3 hours - balanced for stability
        enable_historical: bool = True,
        enable_auto_resolution: bool = True,
        resolution_interval_hours: int = 4,
        enable_twitter: bool = False,  # Disabled by default - requires paid X (Twitter) API
        twitter_interval_hours: int = 6
    ):
        """Start the scheduler (runs in background thread - non-blocking)"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Add jobs
        self.add_rss_job(interval_hours=rss_interval_hours)
        
        if enable_historical:
            self.add_historical_job()
        
        if enable_auto_resolution:
            self.add_auto_resolution_job(interval_hours=resolution_interval_hours)
        
        if enable_twitter:
            self.add_twitter_job(interval_hours=twitter_interval_hours)
        
        # Start scheduler - runs in background thread
        self.scheduler.start()
        self.is_running = True
        logger.info("TrackRecord scheduler started (non-blocking background mode)")
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("TrackRecord scheduler stopped")
    
    def get_status(self) -> dict:
        """Get scheduler status"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            })
        
        with self._lock:
            return {
                "is_running": self.is_running,
                "jobs": jobs,
                "last_run_times": {
                    k: v.isoformat() for k, v in self.last_run_times.items()
                },
                "stats": self.run_stats.copy()
            }
    
    # Async wrappers for manual triggering via API
    async def run_rss_ingestion(self):
        """Async wrapper for manual RSS ingestion - runs in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._run_rss_ingestion_sync)
    
    async def run_historical_collection(self, start_year: int = 2020, max_per_pundit: int = 10):
        """Async wrapper for manual historical collection - runs in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, 
            lambda: self._run_historical_collection_sync(start_year, max_per_pundit)
        )
    
    async def run_auto_resolution(self):
        """Async wrapper for manual auto-resolution - runs in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._run_auto_resolution_sync)
    
    async def run_twitter_collection(self, max_pundits: int = 20):
        """Async wrapper for manual Twitter collection - runs in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor,
            lambda: self._run_twitter_collection_sync(max_pundits)
        )


# Global scheduler instance
_scheduler: Optional[TrackRecordScheduler] = None


def get_scheduler() -> TrackRecordScheduler:
    """Get the global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = TrackRecordScheduler()
    return _scheduler


def start_scheduler():
    """Start the global scheduler"""
    scheduler = get_scheduler()
    scheduler.start()
    return scheduler


def stop_scheduler():
    """Stop the global scheduler"""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
        _scheduler = None
