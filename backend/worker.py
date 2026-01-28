#!/usr/bin/env python3
"""
TrackRecord Background Worker

This is a dedicated worker process that handles all background tasks:
- RSS feed ingestion
- AI prediction extraction
- Auto-resolution (including AI resolution)
- Historical data collection

This runs completely separately from the API, ensuring the API
stays responsive at all times.
"""

import os
import sys
import time
import signal
import logging
import asyncio
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("worker")

# Graceful shutdown handling
shutdown_requested = False

def signal_handler(signum, frame):
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


async def run_rss_ingestion():
    """Run RSS feed ingestion with strict timeout"""
    logger.info("Starting RSS ingestion...")
    
    try:
        # Import inside function to avoid module-level issues
        from database.session import async_session
        from services.auto_agent import AutoAgentPipeline
        
        async def _do_rss():
            async with async_session() as session:
                pipeline = AutoAgentPipeline(session)
                return await pipeline.run_pipeline(max_articles=10)
        
        results = await asyncio.wait_for(_do_rss(), timeout=180)  # 3 minute timeout
        logger.info(f"RSS ingestion complete: {results}")
        return results
        
    except asyncio.TimeoutError:
        logger.error("RSS ingestion timed out after 3 minutes - skipping")
        return {"error": "timeout", "skipped": True}
    except Exception as e:
        logger.error(f"RSS ingestion failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": str(e)}


async def run_auto_resolution():
    """Run auto-resolution including AI resolution"""
    from database.session import async_session
    from services.auto_resolver import run_auto_resolution, get_resolver
    
    logger.info("Starting auto-resolution...")
    
    try:
        async with async_session() as session:
            # Step 1: Standard auto-resolution
            results = await asyncio.wait_for(
                run_auto_resolution(session),
                timeout=180  # 3 minute timeout
            )
            
            standard_resolved = results.get("market_resolved", 0) + results.get("expired_auto_resolved", 0)
            logger.info(f"Standard resolution: {standard_resolved} resolved")
            
            # Step 2: AI resolution
            ai_resolved = 0
            try:
                resolver = get_resolver()
                ai_results = await asyncio.wait_for(
                    resolver.ai_resolve_batch(session, limit=10),
                    timeout=180  # 3 minute timeout
                )
                ai_resolved = ai_results.get("resolved_yes", 0) + ai_results.get("resolved_no", 0)
                logger.info(f"AI resolution: {ai_resolved} resolved")
            except asyncio.TimeoutError:
                logger.warning("AI resolution timed out")
            except Exception as e:
                logger.error(f"AI resolution error: {e}")
            
            return {
                **results,
                "ai_resolved": ai_resolved,
                "total_resolved": standard_resolved + ai_resolved
            }
            
    except asyncio.TimeoutError:
        logger.error("Auto-resolution timed out")
        return {"error": "timeout"}
    except Exception as e:
        logger.error(f"Auto-resolution failed: {e}")
        return {"error": str(e)}


async def run_historical_collection():
    """Run historical data collection (weekly)"""
    from database.session import async_session
    
    logger.info("Starting historical collection...")
    
    try:
        # Check if historical collector exists
        try:
            from services.historical_collector import HistoricalPipeline
        except ImportError:
            logger.warning("Historical collector not available")
            return {"skipped": True, "reason": "not_available"}
        
        async with async_session() as session:
            pipeline = HistoricalPipeline(session)
            results = await asyncio.wait_for(
                pipeline.run(start_year=2020, max_per_pundit=10, auto_process=True),
                timeout=600  # 10 minute timeout
            )
            logger.info(f"Historical collection complete: {results}")
            return results
            
    except asyncio.TimeoutError:
        logger.error("Historical collection timed out")
        return {"error": "timeout"}
    except Exception as e:
        logger.error(f"Historical collection failed: {e}")
        return {"error": str(e)}


def get_schedule_config():
    """Get schedule configuration from environment"""
    return {
        "rss_interval_minutes": int(os.getenv("RSS_INTERVAL_MINUTES", "180")),  # 3 hours
        "resolution_interval_minutes": int(os.getenv("RESOLUTION_INTERVAL_MINUTES", "240")),  # 4 hours
        "historical_enabled": os.getenv("HISTORICAL_ENABLED", "true").lower() == "true",
        "historical_day": os.getenv("HISTORICAL_DAY", "sunday"),  # Day of week
    }


async def main_loop():
    """Main worker loop - runs tasks on schedule"""
    global shutdown_requested
    
    config = get_schedule_config()
    
    logger.info("=" * 50)
    logger.info("TrackRecord Worker Started")
    logger.info("=" * 50)
    logger.info(f"RSS interval: {config['rss_interval_minutes']} minutes")
    logger.info(f"Resolution interval: {config['resolution_interval_minutes']} minutes")
    logger.info(f"Historical collection: {'enabled' if config['historical_enabled'] else 'disabled'}")
    logger.info("=" * 50)
    
    # Track last run times
    last_rss_run = None
    last_resolution_run = None
    last_historical_run = None
    
    # Initial delay to let everything start up
    logger.info("Waiting 30 seconds before starting tasks...")
    await asyncio.sleep(30)
    
    while not shutdown_requested:
        now = datetime.utcnow()
        logger.info(f"Worker loop check at {now.strftime('%H:%M:%S')}")
        
        try:
            # Run RESOLUTION FIRST (most important for user experience)
            resolution_interval = config["resolution_interval_minutes"] * 60
            if last_resolution_run is None or (now - last_resolution_run).total_seconds() >= resolution_interval:
                logger.info("Running auto-resolution task...")
                try:
                    await run_auto_resolution()
                except Exception as e:
                    logger.error(f"Resolution task failed: {e}")
                last_resolution_run = datetime.utcnow()
                logger.info("Auto-resolution task completed")
            
            # Then run RSS (less critical)
            rss_interval = config["rss_interval_minutes"] * 60
            if last_rss_run is None or (now - last_rss_run).total_seconds() >= rss_interval:
                logger.info("Running RSS ingestion task...")
                try:
                    await run_rss_ingestion()
                except Exception as e:
                    logger.error(f"RSS task failed: {e}")
                last_rss_run = datetime.utcnow()
                logger.info("RSS ingestion task completed")
            
            # Historical collection (weekly, least critical)
            if config["historical_enabled"]:
                current_day = now.strftime("%A").lower()
                if current_day == config["historical_day"].lower():
                    if last_historical_run is None or (now - last_historical_run).days >= 1:
                        logger.info("Running historical collection task...")
                        try:
                            await run_historical_collection()
                        except Exception as e:
                            logger.error(f"Historical task failed: {e}")
                        last_historical_run = datetime.utcnow()
                        logger.info("Historical collection task completed")
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        # Sleep for 1 minute before checking again
        logger.info("Sleeping for 60 seconds...")
        for _ in range(60):
            if shutdown_requested:
                break
            await asyncio.sleep(1)
    
    logger.info("Worker shutdown complete")


def main():
    """Entry point"""
    logger.info("Initializing TrackRecord Worker...")
    
    # Verify database connection
    try:
        from database.session import engine
        logger.info("Database connection configured")
    except Exception as e:
        logger.error(f"Database configuration error: {e}")
        sys.exit(1)
    
    # Check for required API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.warning("ANTHROPIC_API_KEY not set - AI resolution will be disabled")
    
    # Run the main loop
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
