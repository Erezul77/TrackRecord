# services/scheduler.py
"""
Background Scheduler Service
Runs automated tasks:
- Historical data collection
- RSS feed ingestion
- Prediction extraction
"""
import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrackRecordScheduler:
    """
    Manages all scheduled background tasks for TrackRecord
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.last_run_times = {}
        self.run_stats = {
            "rss_ingestion": {"runs": 0, "predictions": 0, "errors": 0},
            "historical_collection": {"runs": 0, "articles": 0, "predictions": 0, "errors": 0}
        }
    
    async def run_rss_ingestion(self):
        """Run RSS feed ingestion and prediction extraction"""
        from database.session import async_session
        from services.auto_agent import AutoAgentPipeline
        
        logger.info("Starting scheduled RSS ingestion...")
        self.last_run_times["rss_ingestion"] = datetime.now()
        
        try:
            async with async_session() as session:
                pipeline = AutoAgentPipeline(session)
                results = await pipeline.run_pipeline()
                
                self.run_stats["rss_ingestion"]["runs"] += 1
                self.run_stats["rss_ingestion"]["predictions"] += results.get("new_predictions", 0)
                
                logger.info(f"RSS ingestion complete: {results}")
                return results
                
        except Exception as e:
            self.run_stats["rss_ingestion"]["errors"] += 1
            logger.error(f"RSS ingestion failed: {e}")
            return {"error": str(e)}
    
    async def run_historical_collection(
        self,
        start_year: int = 2020,
        max_per_pundit: int = 10
    ):
        """Run historical data collection"""
        from database.session import async_session
        from services.historical_collector import HistoricalPipeline
        
        logger.info(f"Starting historical collection from {start_year}...")
        self.last_run_times["historical_collection"] = datetime.now()
        
        try:
            async with async_session() as session:
                pipeline = HistoricalPipeline(session)
                results = await pipeline.run(
                    start_year=start_year,
                    max_per_pundit=max_per_pundit,
                    auto_process=True
                )
                
                self.run_stats["historical_collection"]["runs"] += 1
                self.run_stats["historical_collection"]["articles"] += results.get("articles_collected", 0)
                self.run_stats["historical_collection"]["predictions"] += results.get("predictions_extracted", 0)
                
                logger.info(f"Historical collection complete: {results}")
                return results
                
        except Exception as e:
            self.run_stats["historical_collection"]["errors"] += 1
            logger.error(f"Historical collection failed: {e}")
            return {"error": str(e)}
    
    def add_rss_job(self, interval_hours: int = 6):
        """Schedule RSS ingestion job"""
        self.scheduler.add_job(
            self.run_rss_ingestion,
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
            self.run_historical_collection,
            trigger=CronTrigger(hour=cron_hour, day_of_week=cron_day_of_week),
            id="historical_collection",
            name="Historical Data Collection",
            replace_existing=True,
            kwargs={"start_year": start_year, "max_per_pundit": 10}
        )
        logger.info(f"Historical collection scheduled for {cron_day_of_week} at {cron_hour}:00")
    
    def start(
        self,
        rss_interval_hours: int = 6,
        enable_historical: bool = True
    ):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Add jobs
        self.add_rss_job(interval_hours=rss_interval_hours)
        
        if enable_historical:
            self.add_historical_job()
        
        # Start scheduler
        self.scheduler.start()
        self.is_running = True
        logger.info("TrackRecord scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
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
        
        return {
            "is_running": self.is_running,
            "jobs": jobs,
            "last_run_times": {
                k: v.isoformat() for k, v in self.last_run_times.items()
            },
            "stats": self.run_stats
        }


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
