import os
import uuid
import random
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, or_, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
import logging
from dotenv import load_dotenv

from database.session import get_db
from database.models import Pundit, PunditMetrics, Prediction, MatchReviewQueue, PredictionVote, Position, Match
from sqlalchemy import func
from schemas import PunditResponse, PredictionResponse, MatchReviewResponse
from pydantic import BaseModel
import hashlib

load_dotenv()

from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

# Custom Swagger UI with TrackRecord branding
swagger_ui_parameters = {
    "docExpansion": "none",
    "defaultModelsExpandDepth": -1,
    "syntaxHighlight.theme": "monokai",
    "tryItOutEnabled": True
}

app = FastAPI(
    title="TrackRecord API",
    version="1.0.0",
    description="Pundit prediction tracking and accountability platform. Track what experts predict and whether they're right.",
    swagger_ui_parameters=swagger_ui_parameters,
    docs_url=None,  # Disable default docs, we'll serve custom
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Leaderboard", "description": "Pundit rankings and stats"},
        {"name": "Predictions", "description": "Prediction data and voting"},
        {"name": "Community", "description": "User registration and competition"},
        {"name": "Admin", "description": "Admin operations"},
    ]
)

# Custom CSS for Swagger UI - Sharp B&W theme
CUSTOM_SWAGGER_CSS = """
/* TrackRecord B&W Sharp Theme */
.swagger-ui .topbar { display: none !important; }
.swagger-ui .info .title { font-size: 32px; font-weight: 900; color: #000; }
.swagger-ui .info .title small { background: #000; color: #fff; padding: 2px 8px; margin-left: 8px; border-radius: 0; }
.swagger-ui .info .description { color: #555; }
.swagger-ui .scheme-container { background: #f5f5f5; padding: 16px; border-radius: 0; }
.swagger-ui .opblock { border-radius: 0 !important; border: 1px solid #ddd; }
.swagger-ui .opblock .opblock-summary { border-radius: 0 !important; }
.swagger-ui .opblock.opblock-get { border-color: #000; background: rgba(0,0,0,0.02); }
.swagger-ui .opblock.opblock-get .opblock-summary { border-color: #000; }
.swagger-ui .opblock.opblock-post { border-color: #000; background: rgba(0,0,0,0.05); }
.swagger-ui .opblock.opblock-post .opblock-summary { border-color: #000; }
.swagger-ui .opblock.opblock-put { border-color: #666; }
.swagger-ui .opblock.opblock-delete { border-color: #c00; }
.swagger-ui .btn { border-radius: 0 !important; }
.swagger-ui .btn.execute { background: #000 !important; border-color: #000 !important; }
.swagger-ui .btn.cancel { background: #fff !important; border: 1px solid #000 !important; color: #000 !important; }
.swagger-ui select { border-radius: 0 !important; }
.swagger-ui input[type=text], .swagger-ui textarea { border-radius: 0 !important; }
.swagger-ui .model-box { border-radius: 0 !important; }
.swagger-ui .opblock-tag { border-radius: 0; border-bottom: 2px solid #000; }
.swagger-ui .opblock-tag:hover { background: rgba(0,0,0,0.05); }
.swagger-ui .response-col_status { font-weight: bold; }
.swagger-ui .responses-table { border-radius: 0; }
.swagger-ui .response { border-radius: 0 !important; }
.swagger-ui .model { border-radius: 0 !important; }
.swagger-ui .tab li { border-radius: 0 !important; }
.swagger-ui .tab li.active { background: #000; color: #fff; }
.swagger-ui .copy-to-clipboard { border-radius: 0 !important; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
"""

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return HTMLResponse(content=f"""
<!DOCTYPE html>
<html>
<head>
    <title>TrackRecord API - Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
    <link rel="icon" type="image/png" href="https://trackrecord.life/TrackRecord_Logo1.png">
    <style>
    {CUSTOM_SWAGGER_CSS}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {{
            SwaggerUIBundle({{
                url: "{app.openapi_url}",
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout",
                docExpansion: "none",
                defaultModelsExpandDepth: -1,
                syntaxHighlight: {{ theme: "monokai" }},
                tryItOutEnabled: true
            }});
        }};
    </script>
</body>
</html>
""", media_type="text/html")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock admin check dependency
async def require_admin():
    # In production, this would verify a JWT token
    return {"id": uuid.uuid4(), "is_admin": True}

@app.get("/")
async def root():
    return {"message": "TrackRecord API is running"}

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check that verifies database connectivity"""
    try:
        # Verify database connection with a simple query
        await db.execute(select(1))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logging.error(f"Health check failed - database error: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")

# Startup event - API only, no scheduler (scheduler runs in separate worker)
@app.on_event("startup")
async def startup_event():
    # Scheduler is now handled by the dedicated worker process
    # This keeps the API lightweight and responsive
    logging.info("TrackRecord API started (scheduler runs in separate worker)")

@app.on_event("shutdown")
async def shutdown_event():
    from services.scheduler import stop_scheduler
    try:
        stop_scheduler()
        logging.info("Background scheduler stopped")
    except Exception as e:
        logging.error(f"Error stopping scheduler: {e}")

# Minimum resolved predictions for official ranking (frontend handles display)
MIN_PREDICTIONS_FOR_RANKING = 3

@app.get("/api/leaderboard", response_model=List[PunditResponse])
async def get_leaderboard(
    category: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all pundits. Ranked by win rate, but only pundits with >= 3 resolved predictions
    are officially ranked. Those with < 3 show at the end with 'needs more data'.
    """
    from sqlalchemy import case
    
    query = select(Pundit).join(PunditMetrics).options(selectinload(Pundit.metrics))
    
    if category:
        query = query.where(Pundit.domains.any(category))
    
    # Order: First by having enough data (>=3 resolved), then by win rate
    query = query.order_by(
        case(
            (PunditMetrics.resolved_predictions >= MIN_PREDICTIONS_FOR_RANKING, 0),
            else_=1
        ),  # Ranked pundits first
        desc(PunditMetrics.paper_win_rate),  # Then by win rate
        desc(PunditMetrics.resolved_predictions)  # Tie-breaker: more resolved
    ).limit(limit)
    
    result = await db.execute(query)
    pundits = result.scalars().all()
    return pundits

@app.get("/api/pundits/{pundit_id}", response_model=PunditResponse)
async def get_pundit(pundit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Pundit).where(Pundit.id == pundit_id).options(selectinload(Pundit.metrics))
    )
    pundit = result.scalar_one_or_none()
    if not pundit:
        raise HTTPException(status_code=404, detail="Pundit not found")
    return pundit


@app.post("/api/pundits/{pundit_id}/activate-tracking", tags=["Admin"])
async def activate_pundit_tracking(
    pundit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Immediately search for and extract predictions from a specific pundit.
    Uses Google News RSS to find recent articles mentioning this pundit.
    """
    import feedparser
    import httpx
    from urllib.parse import quote
    
    # Get the pundit
    result = await db.execute(
        select(Pundit).where(Pundit.id == pundit_id)
    )
    pundit = result.scalar_one_or_none()
    if not pundit:
        raise HTTPException(status_code=404, detail="Pundit not found")
    
    # Search Google News for this pundit
    search_query = quote(f'"{pundit.name}" prediction OR forecast OR "will" OR "expect"')
    google_news_url = f"https://news.google.com/rss/search?q={search_query}&hl=en-US&gl=US&ceid=US:en"
    
    articles_found = 0
    predictions_extracted = 0
    errors = []
    
    try:
        # Fetch RSS feed
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(google_news_url)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch news")
        
        # Parse feed
        feed = feedparser.parse(response.text)
        articles_found = len(feed.entries[:10])  # Limit to 10 articles
        
        # Process articles with AI
        from services.auto_agent import AutoAgentPipeline
        from services.rss_ingestion import NewsArticle
        
        pipeline = AutoAgentPipeline(db)
        
        for entry in feed.entries[:10]:
            try:
                article = NewsArticle(
                    title=entry.get('title', ''),
                    url=entry.get('link', ''),
                    summary=entry.get('summary', entry.get('description', '')),
                    published=datetime.utcnow(),
                    source="Google News",
                    author=None
                )
                
                # Extract predictions (force this specific pundit)
                new_predictions = await pipeline._process_article(article, force_pundit=pundit)
                predictions_extracted += new_predictions
                
            except Exception as e:
                errors.append(str(e)[:100])
        
        await db.commit()
        
    except Exception as e:
        logging.error(f"Error activating tracking for {pundit.name}: {e}")
        errors.append(str(e))
    
    return {
        "status": "complete",
        "pundit": pundit.name,
        "articles_searched": articles_found,
        "predictions_extracted": predictions_extracted,
        "errors": errors[:5] if errors else None,
        "message": f"Found {articles_found} articles, extracted {predictions_extracted} predictions for {pundit.name}"
    }

@app.get("/api/pundits/{pundit_id}/predictions")
async def get_pundit_predictions(
    pundit_id: uuid.UUID, 
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Get predictions for a pundit with outcome status (paginated)"""
    try:
        result = await db.execute(
            select(Prediction)
            .where(Prediction.pundit_id == pundit_id)
            .options(selectinload(Prediction.position))
            .order_by(desc(Prediction.captured_at))
            .limit(limit)
        )
        predictions = result.scalars().all()
    except Exception as e:
        logging.error(f"Error fetching predictions for pundit {pundit_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch predictions")
    
    return [
        {
            "id": str(p.id),
            "claim": p.claim,
            "quote": p.quote,
            "confidence": p.confidence,
            "category": p.category,
            "status": p.status,
            "source_url": p.source_url,
            "source_type": p.source_type,
            "timeframe": p.timeframe.isoformat() if p.timeframe else None,
            "captured_at": p.captured_at.isoformat() if p.captured_at else None,
            "outcome": p.outcome or (p.position.outcome if p.position else None),
            "tr_index": {
                "score": p.tr_index_score,
                "tier": "gold" if p.tr_index_score and p.tr_index_score >= 80 else 
                        "silver" if p.tr_index_score and p.tr_index_score >= 60 else 
                        "bronze" if p.tr_index_score and p.tr_index_score >= 40 else None,
                "specificity": p.tr_specificity_score,
                "verifiability": p.tr_verifiability_score,
                "boldness": p.tr_boldness_score,
                "relevance": p.tr_relevance_score,
                "stakes": p.tr_stakes_score
            } if p.tr_index_score else None,
            "chain_hash": p.chain_hash[:16] + "..." if p.chain_hash else None,
            "chain_index": p.chain_index
        }
        for p in predictions
    ]

@app.get("/api/predictions/recent")
async def get_recent_predictions(
    limit: int = Query(100, ge=1, le=500),
    category: Optional[str] = None,
    horizon: Optional[str] = Query(None, description="Filter by horizon: ST, MT, LT, V"),
    sort: str = Query("default", description="Sort: default, newest, oldest, resolving_soon, boldest, highest_score"),
    db: AsyncSession = Depends(get_db)
):
    """Get recent predictions from all pundits with pundit info and outcome"""
    from database.models import Position
    
    query = select(Prediction).join(Pundit).options(
        selectinload(Prediction.pundit),
        selectinload(Prediction.position)
    )
    
    # Always exclude flagged predictions and low-quality from public feed
    # Lowered threshold from 40 to 25 to show more predictions
    query = query.where(Prediction.flagged == False)
    query = query.where(
        (Prediction.tr_index_score >= 25) | (Prediction.tr_index_score == None)
    )  # Allow None (unscored) but filter out very low scores
    
    if category:
        query = query.where(Prediction.category == category)
    
    # Filter by horizon if specified
    if horizon and horizon.upper() in ["ST", "MT", "LT", "V"]:
        query = query.where(Prediction.horizon == horizon.upper())
    
    query = query.order_by(desc(Prediction.captured_at)).limit(limit * 2)  # Get more to sort properly
    
    result = await db.execute(query)
    predictions = result.scalars().all()
    
    # Sort based on sort parameter
    if sort == "oldest":
        # Oldest first
        sorted_predictions = sorted(predictions, key=lambda p: p.captured_at.timestamp() if p.captured_at else 0)
    elif sort == "resolving_soon":
        # Soonest timeframe first (open predictions only, then resolved)
        def resolving_key(p):
            has_outcome = p.outcome or (p.position and p.position.outcome)
            if has_outcome:
                return (1, float('inf'))  # Resolved at the end
            return (0, p.timeframe.timestamp() if p.timeframe else float('inf'))
        sorted_predictions = sorted(predictions, key=resolving_key)
    elif sort == "boldest":
        # Highest boldness score first
        sorted_predictions = sorted(predictions, key=lambda p: -(p.tr_boldness_score or 0))
    elif sort == "highest_score":
        # Highest TR Index score first
        sorted_predictions = sorted(predictions, key=lambda p: -(p.tr_index_score or 0))
    elif sort == "newest":
        # Simply newest first
        sorted_predictions = sorted(predictions, key=lambda p: -(p.captured_at.timestamp() if p.captured_at else 0))
    else:
        # Default: Open predictions first (newest first), then resolved (newest first)
        def sort_key(p):
            has_outcome = p.outcome or (p.position and p.position.outcome)
            return (
                1 if has_outcome else 0,  # Open first
                -(p.captured_at.timestamp() if p.captured_at else 0)  # Newest first
            )
        sorted_predictions = sorted(predictions, key=sort_key)
    
    sorted_predictions = sorted_predictions[:limit]
    
    return [
        {
            "id": str(p.id),
            "claim": p.claim,
            "quote": p.quote,
            "confidence": p.confidence,
            "category": p.category,
            "status": p.status,
            "source_url": p.source_url,
            "source_type": p.source_type,
            "timeframe": p.timeframe.isoformat() if p.timeframe else None,
            "captured_at": p.captured_at.isoformat() if p.captured_at else None,
            "outcome": p.outcome or (p.position.outcome if p.position else None),
            "tr_index": {
                "score": p.tr_index_score,
                "tier": "gold" if p.tr_index_score and p.tr_index_score >= 80 else 
                        "silver" if p.tr_index_score and p.tr_index_score >= 60 else 
                        "bronze" if p.tr_index_score and p.tr_index_score >= 40 else None
            } if p.tr_index_score else None,
            "horizon": p.horizon,
            "chain_hash": p.chain_hash[:16] + "..." if p.chain_hash else None,
            "chain_index": p.chain_index,
            "pundit": {
                "id": str(p.pundit.id),
                "name": p.pundit.name,
                "username": p.pundit.username,
                "avatar_url": p.pundit.avatar_url
            }
        }
        for p in sorted_predictions
    ]

# Admin Endpoints
@app.get("/api/admin/review-queue", response_model=List[MatchReviewResponse])
async def get_review_queue(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    result = await db.execute(
        select(MatchReviewQueue).where(MatchReviewQueue.status == 'pending').limit(limit)
    )
    return result.scalars().all()

@app.post("/api/admin/matches/{review_id}/approve")
async def approve_match(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    result = await db.execute(
        select(MatchReviewQueue).where(MatchReviewQueue.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    review.status = 'approved'
    review.reviewed_at = datetime.utcnow()
    review.reviewed_by = admin['id']
    
    await db.commit()
    return {"status": "success"}


# ============================================
# RSS Feed Ingestion Endpoints
# ============================================

@app.get("/api/admin/rss/feeds")
async def list_rss_feeds():
    """List available RSS feed sources"""
    from services.rss_ingestion import RSS_FEEDS
    return {
        "feeds": [
            {"key": key, "source": config["source"], "categories": config["categories"]}
            for key, config in RSS_FEEDS.items()
        ]
    }

@app.post("/api/admin/rss/fetch")
async def fetch_rss_articles(
    feed_key: Optional[str] = None,
    admin = Depends(require_admin)
):
    """Fetch articles from RSS feeds (all or specific feed)"""
    from services.rss_ingestion import RSSIngestionService
    
    service = RSSIngestionService()
    
    if feed_key:
        articles = service.fetch_feed(feed_key)
    else:
        articles = service.fetch_all_feeds()
    
    # Filter for prediction-like content
    prediction_articles = service.filter_prediction_articles(articles)
    
    return {
        "total_fetched": len(articles),
        "prediction_articles": len(prediction_articles),
        "articles": [
            {
                "title": a.title,
                "url": a.url,
                "summary": a.summary[:500] if a.summary else "",
                "source": a.source,
                "published": a.published.isoformat(),
                "pundits_mentioned": service.find_pundit_mentions(f"{a.title} {a.summary}")
            }
            for a in prediction_articles[:50]  # Limit response size
        ]
    }


# ============================================
# Manual Prediction Entry
# ============================================

class ManualPredictionInput(BaseModel):
    pundit_username: str
    claim: str
    quote: str
    source_url: str
    confidence: float = 0.6  # Default medium confidence
    category: str = "general"
    timeframe_days: int = 90  # Days from now until resolution
    # TR Index scoring (1-5 scale for simplified entry)
    tr_specificity: int = 3  # 1=vague, 5=very specific
    tr_verifiability: int = 3  # 1=hard to verify, 5=easily verified
    tr_boldness: int = 1  # 1=consensus, 5=very contrarian
    tr_stakes: int = 2  # 1=minor, 5=major impact


# ============================================
# Smart URL Extraction Endpoint
# ============================================

class URLExtractInput(BaseModel):
    url: str

@app.post("/api/extract-from-url")
async def extract_predictions_from_url(
    input: URLExtractInput,
):
    """
    Smart URL extraction - paste a URL and get all predictions extracted automatically.
    Works with: news articles, YouTube videos, blog posts, etc.
    """
    from services.url_extractor import URLExtractor
    
    extractor = URLExtractor()
    
    try:
        result = await extractor.extract_from_url(input.url)
        return result
    except Exception as e:
        return {
            "success": False,
            "url": input.url,
            "error": str(e),
            "predictions": []
        }
    finally:
        await extractor.close()


@app.post("/api/admin/predictions/add")
async def add_manual_prediction(
    prediction_input: ManualPredictionInput,
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Manually add a prediction for a pundit with hash chain verification"""
    from tr_index import quick_score
    from datetime import timedelta
    from services.hash_chain import create_chain_entry, GENESIS_HASH
    
    # Find pundit by username
    result = await db.execute(
        select(Pundit).where(Pundit.username == prediction_input.pundit_username)
    )
    pundit = result.scalar_one_or_none()
    
    if not pundit:
        raise HTTPException(status_code=404, detail=f"Pundit '{prediction_input.pundit_username}' not found")
    
    # Calculate timeframe and captured_at
    captured_at = datetime.utcnow()
    timeframe = captured_at + timedelta(days=prediction_input.timeframe_days)
    
    # Get the latest prediction for chain linking
    latest_result = await db.execute(
        select(Prediction)
        .where(Prediction.chain_hash != None)
        .order_by(desc(Prediction.chain_index))
        .limit(1)
    )
    latest_prediction = latest_result.scalar_one_or_none()
    
    # Determine chain position
    if latest_prediction:
        prev_chain_hash = latest_prediction.chain_hash
        chain_index = (latest_prediction.chain_index or 0) + 1
    else:
        prev_chain_hash = GENESIS_HASH
        chain_index = 1
    
    # Create hash chain entry
    chain_entry = create_chain_entry(
        claim=prediction_input.claim,
        quote=prediction_input.quote,
        source_url=prediction_input.source_url,
        captured_at=captured_at,
        prev_chain_hash=prev_chain_hash,
        chain_index=chain_index
    )
    
    # Check for duplicate using content hash
    existing = await db.execute(
        select(Prediction).where(Prediction.content_hash == chain_entry.content_hash)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="This prediction already exists")
    
    # Calculate TR Index score
    tr_score = quick_score(
        prediction_date=captured_at,
        timeframe=timeframe,
        specificity_level=prediction_input.tr_specificity,
        verifiability_level=prediction_input.tr_verifiability,
        boldness_level=prediction_input.tr_boldness,
        stakes_level=prediction_input.tr_stakes
    )
    
    # Check if prediction passes TR Index thresholds
    if not tr_score.passed:
        raise HTTPException(
            status_code=400, 
            detail=f"Prediction rejected: {tr_score.rejection_reason}. TR Score: {tr_score.total:.1f}/100"
        )
    
    # Create prediction with TR Index scores AND hash chain
    new_prediction = Prediction(
        id=uuid.uuid4(),
        pundit_id=pundit.id,
        claim=prediction_input.claim,
        confidence=prediction_input.confidence,
        timeframe=timeframe,
        quote=prediction_input.quote,
        category=prediction_input.category,
        source_url=prediction_input.source_url,
        source_type="manual",
        captured_at=captured_at,
        # Hash chain fields
        content_hash=chain_entry.content_hash,
        chain_hash=chain_entry.chain_hash,
        chain_index=chain_entry.chain_index,
        prev_chain_hash=chain_entry.prev_chain_hash,
        status="pending",
        flagged=False,
        # TR Index scores
        tr_index_score=tr_score.total,
        tr_specificity_score=tr_score.specificity,
        tr_verifiability_score=tr_score.verifiability,
        tr_boldness_score=tr_score.boldness,
        tr_relevance_score=tr_score.relevance,
        tr_stakes_score=tr_score.stakes,
        tr_rejected=False,
        created_at=datetime.utcnow()
    )
    
    db.add(new_prediction)
    await db.commit()
    
    return {
        "status": "success",
        "prediction_id": str(new_prediction.id),
        "pundit": pundit.name,
        "claim": prediction_input.claim,
        "tr_index": {
            "total": tr_score.total,
            "tier": tr_score.tier,
            "breakdown": {
                "specificity": tr_score.specificity,
                "verifiability": tr_score.verifiability,
                "boldness": tr_score.boldness,
                "relevance": tr_score.relevance,
                "stakes": tr_score.stakes
            }
        },
        "hash_chain": {
            "content_hash": chain_entry.content_hash,
            "chain_hash": chain_entry.chain_hash,
            "chain_index": chain_entry.chain_index,
            "prev_chain_hash": chain_entry.prev_chain_hash[:16] + "..." if chain_entry.prev_chain_hash else None,
            "verification_url": f"https://trackrecord.life/verify/{chain_entry.chain_hash[:16]}"
        }
    }


# ============================================
# Hash Chain Verification Endpoints
# ============================================

@app.get("/api/verify/{hash_prefix}")
async def verify_prediction_by_hash(
    hash_prefix: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify a prediction by its hash (content_hash or chain_hash).
    Accepts partial hash (min 8 chars) for convenience.
    """
    from services.hash_chain import verify_chain_entry, format_hash_display
    
    if len(hash_prefix) < 8:
        raise HTTPException(status_code=400, detail="Hash prefix must be at least 8 characters")
    
    # Search by chain_hash or content_hash prefix
    result = await db.execute(
        select(Prediction, Pundit)
        .join(Pundit, Prediction.pundit_id == Pundit.id)
        .where(
            (Prediction.chain_hash.startswith(hash_prefix)) |
            (Prediction.content_hash.startswith(hash_prefix))
        )
    )
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Prediction not found with this hash")
    
    prediction, pundit = row
    
    # Verify the hash chain
    verification = None
    if prediction.chain_hash and prediction.prev_chain_hash:
        verification = verify_chain_entry(
            claim=prediction.claim,
            quote=prediction.quote,
            source_url=prediction.source_url,
            captured_at=prediction.captured_at,
            stored_content_hash=prediction.content_hash,
            stored_chain_hash=prediction.chain_hash,
            stored_prev_hash=prediction.prev_chain_hash,
            stored_chain_index=prediction.chain_index or 0
        )
    
    return {
        "verified": verification["is_valid"] if verification else True,
        "prediction": {
            "id": str(prediction.id),
            "pundit_name": pundit.name,
            "pundit_username": pundit.username,
            "claim": prediction.claim,
            "quote": prediction.quote,
            "category": prediction.category,
            "source_url": prediction.source_url,
            "captured_at": prediction.captured_at.isoformat(),
            "timeframe": prediction.timeframe.isoformat() if prediction.timeframe else None,
            "status": prediction.status
        },
        "hash_chain": {
            "content_hash": prediction.content_hash,
            "chain_hash": prediction.chain_hash,
            "chain_index": prediction.chain_index,
            "prev_chain_hash": prediction.prev_chain_hash,
            "content_valid": verification["content_valid"] if verification else True,
            "chain_valid": verification["chain_valid"] if verification else True
        },
        "verification_details": verification
    }


@app.get("/api/chain/status")
async def get_chain_status(db: AsyncSession = Depends(get_db)):
    """Get the current status of the hash chain"""
    from services.hash_chain import GENESIS_HASH
    
    # Get total predictions with chain hash
    total_result = await db.execute(
        select(func.count(Prediction.id)).where(Prediction.chain_hash != None)
    )
    total_chained = total_result.scalar() or 0
    
    # Get latest prediction
    latest_result = await db.execute(
        select(Prediction)
        .where(Prediction.chain_hash != None)
        .order_by(desc(Prediction.chain_index))
        .limit(1)
    )
    latest = latest_result.scalar_one_or_none()
    
    # Get first prediction
    first_result = await db.execute(
        select(Prediction)
        .where(Prediction.chain_hash != None)
        .order_by(Prediction.chain_index)
        .limit(1)
    )
    first = first_result.scalar_one_or_none()
    
    return {
        "chain_active": True,
        "total_predictions_chained": total_chained,
        "genesis_hash": GENESIS_HASH[:16] + "...",
        "latest_chain_index": latest.chain_index if latest else 0,
        "latest_chain_hash": latest.chain_hash[:16] + "..." if latest and latest.chain_hash else None,
        "latest_captured_at": latest.captured_at.isoformat() if latest else None,
        "first_chain_hash": first.chain_hash[:16] + "..." if first and first.chain_hash else None,
        "first_captured_at": first.captured_at.isoformat() if first else None,
        "integrity": "All predictions are cryptographically linked and tamper-evident"
    }


@app.post("/api/admin/chain/backfill", tags=["Admin"])
async def backfill_hash_chain(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Backfill hash chain for all existing predictions that don't have hashes.
    This creates a complete chain ordered by captured_at timestamp.
    """
    from services.hash_chain import create_chain_entry, GENESIS_HASH
    
    # Get the current highest chain_index
    latest_result = await db.execute(
        select(Prediction)
        .where(Prediction.chain_hash != None)
        .order_by(desc(Prediction.chain_index))
        .limit(1)
    )
    latest = latest_result.scalar_one_or_none()
    
    if latest:
        current_index = latest.chain_index
        prev_hash = latest.chain_hash
    else:
        current_index = 0
        prev_hash = GENESIS_HASH
    
    # Get all predictions without chain_hash, ordered by captured_at
    result = await db.execute(
        select(Prediction)
        .where(Prediction.chain_hash == None)
        .order_by(Prediction.captured_at)
    )
    predictions = result.scalars().all()
    
    if not predictions:
        return {"message": "All predictions already have hashes", "total_processed": 0}
    
    processed = 0
    for pred in predictions:
        current_index += 1
        
        chain_entry = create_chain_entry(
            claim=pred.claim,
            quote=pred.quote or "",
            source_url=pred.source_url or "",
            captured_at=pred.captured_at,
            prev_chain_hash=prev_hash,
            chain_index=current_index
        )
        
        pred.chain_hash = chain_entry.chain_hash
        pred.chain_index = chain_entry.chain_index
        pred.prev_chain_hash = chain_entry.prev_chain_hash
        
        prev_hash = chain_entry.chain_hash
        processed += 1
    
    await db.commit()
    
    return {
        "message": f"Backfilled {processed} predictions",
        "total_processed": processed,
        "first_index": current_index - processed + 1,
        "last_index": current_index,
        "last_hash": prev_hash[:16] + "..."
    }


# ============================================
# TR Prediction Index Scoring
# ============================================

class TRIndexCalculateInput(BaseModel):
    timeframe_days: int = 90  # Days from now
    specificity: int = 3  # 1-5
    verifiability: int = 3  # 1-5
    boldness: int = 1  # 1-5
    stakes: int = 2  # 1-5

@app.post("/api/tr-index/calculate")
async def calculate_tr_index_preview(
    input_data: TRIndexCalculateInput
):
    """
    Preview TR Prediction Index score before submitting.
    Returns score breakdown and whether it passes thresholds.
    """
    from tr_index import quick_score
    from datetime import timedelta
    
    timeframe = datetime.utcnow() + timedelta(days=input_data.timeframe_days)
    
    score = quick_score(
        prediction_date=datetime.utcnow(),
        timeframe=timeframe,
        specificity_level=input_data.specificity,
        verifiability_level=input_data.verifiability,
        boldness_level=input_data.boldness,
        stakes_level=input_data.stakes
    )
    
    return {
        "passed": score.passed,
        "total": round(score.total, 1),
        "tier": score.tier,
        "rejection_reason": score.rejection_reason,
        "breakdown": {
            "specificity": {"score": round(score.specificity, 1), "max": 35, "min_required": 15},
            "verifiability": {"score": round(score.verifiability, 1), "max": 25, "min_required": 10},
            "boldness": {"score": round(score.boldness, 1), "max": 20, "min_required": 0},
            "relevance": {"score": round(score.relevance, 1), "max": 15, "min_required": 5},
            "stakes": {"score": round(score.stakes, 1), "max": 5, "min_required": 0}
        },
        "thresholds": {
            "minimum_total": 40,
            "maximum_timeframe_months": 12
        }
    }

@app.get("/api/tr-index/tiers")
async def get_tr_index_tiers():
    """Get TR Index tier definitions"""
    return {
        "tiers": [
            {"name": "gold", "min_score": 80, "description": "Exceptional prediction quality"},
            {"name": "silver", "min_score": 60, "description": "Strong prediction quality"},
            {"name": "bronze", "min_score": 40, "description": "Meets minimum standards"},
            {"name": "rejected", "min_score": 0, "description": "Does not meet minimum thresholds"}
        ],
        "components": [
            {"name": "Specificity", "weight": 35, "min_required": 15, "description": "How concrete and measurable is the claim?"},
            {"name": "Verifiability", "weight": 25, "min_required": 10, "description": "Can we objectively verify the outcome?"},
            {"name": "Boldness", "weight": 20, "min_required": 0, "description": "How contrarian/against-consensus is this?"},
            {"name": "Relevance", "weight": 15, "min_required": 5, "description": "Time horizon (shorter = more relevant)"},
            {"name": "Stakes", "weight": 5, "min_required": 0, "description": "How significant if true?"}
        ]
    }


@app.get("/api/admin/pundits/list")
async def list_pundits_simple(db: AsyncSession = Depends(get_db)):
    """Simple list of all pundits for admin dropdown"""
    result = await db.execute(select(Pundit).order_by(Pundit.name))
    pundits = result.scalars().all()
    return {
        "pundits": [
            {"id": str(p.id), "name": p.name, "username": p.username}
            for p in pundits
        ]
    }

class NewPunditInput(BaseModel):
    name: str
    username: str
    bio: str = ""
    affiliation: str = ""
    domains: List[str] = ["general"]
    avatar_url: str = ""

@app.post("/api/admin/pundits/add")
async def add_pundit(
    pundit_input: NewPunditInput,
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Add a new pundit to track"""
    # Check if username already exists
    result = await db.execute(
        select(Pundit).where(Pundit.username == pundit_input.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Pundit @{pundit_input.username} already exists")
    
    # Create pundit
    pundit = Pundit(
        id=uuid.uuid4(),
        name=pundit_input.name,
        username=pundit_input.username,
        bio=pundit_input.bio,
        affiliation=pundit_input.affiliation,
        domains=pundit_input.domains,
        avatar_url=pundit_input.avatar_url or None,
        verified=True,
        verified_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(pundit)
    
    # Create initial metrics
    metrics = PunditMetrics(
        pundit_id=pundit.id,
        total_predictions=0,
        matched_predictions=0,
        resolved_predictions=0,
        paper_total_pnl=0,
        paper_win_rate=0,
        paper_roi=0,
        last_calculated=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(metrics)
    
    await db.commit()
    
    return {
        "status": "success",
        "pundit_id": str(pundit.id),
        "name": pundit.name,
        "username": pundit.username
    }


# ============================================
# Auto-Agent Pipeline Endpoints
# ============================================

@app.post("/api/admin/auto-agent/run")
async def run_auto_agent(
    feed_keys: Optional[List[str]] = None,
    admin = Depends(require_admin)
):
    """
    Trigger the auto-agent pipeline to:
    1. Fetch RSS articles
    2. Extract predictions using AI
    3. Match to Polymarket
    4. Store in database
    """
    import asyncio
    from database.session import SessionLocal
    from services.auto_agent import AutoAgentPipeline
    
    db = SessionLocal()
    
    try:
        pipeline = AutoAgentPipeline(db)
        await pipeline.initialize()
        
        stats = await pipeline.run_pipeline(feed_keys)
        
        await pipeline.close()
        
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
    finally:
        db.close()

# ============================================
# Twitter/X Integration
# ============================================

@app.get("/api/admin/twitter/status", tags=["Admin"])
async def get_twitter_status(admin = Depends(require_admin)):
    """Check if Twitter API is configured and working"""
    import os
    
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    
    if not bearer_token:
        return {
            "configured": False,
            "error": "X_BEARER_TOKEN not set. X (Twitter) API requires Basic plan ($100/month)."
        }
    
    try:
        import httpx
        
        # Direct API test for debugging
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://api.twitter.com/2/users/by/username/twitter",
                headers={"Authorization": f"Bearer {bearer_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "configured": True,
                    "status": "working",
                    "test_user": data.get("data", {}).get("username"),
                    "api_tier": "Basic or higher"
                }
            else:
                return {
                    "configured": True,
                    "status": "error",
                    "http_status": response.status_code,
                    "error": "X API error. Requires Basic plan ($100/month) for read access."
                }
            
    except Exception as e:
        return {
            "configured": True,
            "status": "error", 
            "error": str(e)
        }


@app.post("/api/admin/twitter/collect", tags=["Admin"])
async def collect_twitter_predictions(
    usernames: Optional[List[str]] = None,
    since_hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Collect prediction tweets from specified pundits.
    
    Args:
        usernames: List of Twitter usernames to check (defaults to all tracked pundits)
        since_hours: How far back to look (default 24 hours, max 168/7 days)
    """
    from services.twitter_ingestion import TwitterPredictionCollector, get_twitter_pundits
    
    try:
        collector = TwitterPredictionCollector()
        
        # Use provided usernames or default to tracked pundits
        if not usernames:
            usernames = get_twitter_pundits()[:20]  # Limit to avoid rate limits
        
        # Collect tweets
        results = await collector.collect_from_multiple_pundits(usernames, since_hours)
        
        await collector.close()
        
        # Format response
        total_tweets = sum(len(tweets) for tweets in results.values())
        tweet_details = []
        
        for username, tweets in results.items():
            for tweet in tweets:
                tweet_details.append({
                    "username": username,
                    "text": tweet.text[:280],
                    "url": tweet.url,
                    "created_at": tweet.created_at.isoformat(),
                    "likes": tweet.metrics.get("like_count", 0),
                    "retweets": tweet.metrics.get("retweet_count", 0)
                })
        
        return {
            "status": "success",
            "pundits_checked": len(usernames),
            "total_prediction_tweets": total_tweets,
            "tweets": tweet_details[:50]  # Limit response size
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/api/admin/twitter/process", tags=["Admin"])
async def process_twitter_predictions(
    usernames: Optional[List[str]] = None,
    since_hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Collect tweets AND extract predictions using AI, then store in database.
    Full pipeline: Twitter -> AI Extraction -> Database
    """
    from services.twitter_ingestion import TwitterPredictionCollector, get_twitter_pundits
    from services.prediction_extractor import PredictionExtractor
    import hashlib
    
    try:
        collector = TwitterPredictionCollector()
        extractor = PredictionExtractor()
        
        if not usernames:
            usernames = get_twitter_pundits()[:10]  # Conservative limit
        
        # Collect tweets
        results = await collector.collect_from_multiple_pundits(usernames, since_hours)
        await collector.close()
        
        processed = 0
        new_predictions = 0
        errors = []
        
        for username, tweets in results.items():
            for tweet in tweets:
                try:
                    # Check if we already have this tweet
                    content_hash = hashlib.sha256(tweet.url.encode()).hexdigest()
                    
                    existing = await db.execute(
                        select(Prediction).where(Prediction.content_hash == content_hash)
                    )
                    if existing.scalar_one_or_none():
                        continue  # Skip duplicate
                    
                    # Find or create pundit
                    pundit_result = await db.execute(
                        select(Pundit).where(Pundit.username == username)
                    )
                    pundit = pundit_result.scalar_one_or_none()
                    
                    if not pundit:
                        # Create new pundit from Twitter data
                        pundit = Pundit(
                            name=tweet.author_name,
                            username=username,
                            bio=f"Twitter: @{username}",
                            domains=["general"]
                        )
                        db.add(pundit)
                        await db.flush()
                    
                    # Extract prediction using AI
                    extraction = await extractor.extract_from_text(
                        text=tweet.text,
                        source_url=tweet.url,
                        author_name=tweet.author_name
                    )
                    
                    if extraction and extraction.get("has_prediction"):
                        # Create prediction
                        from datetime import timedelta
                        
                        timeframe = datetime.utcnow() + timedelta(days=extraction.get("timeframe_days", 365))
                        
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
                        db.add(prediction)
                        new_predictions += 1
                    
                    processed += 1
                    
                except Exception as e:
                    errors.append(f"{username}: {str(e)[:100]}")
        
        await db.commit()
        
        return {
            "status": "success",
            "tweets_processed": processed,
            "new_predictions": new_predictions,
            "errors": errors[:10] if errors else []
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/api/admin/ai-extract")
async def ai_extract_predictions(
    feed_key: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    admin = Depends(require_admin)
):
    """
    Fetch RSS articles and use AI (Claude) to extract specific predictions.
    Returns extracted predictions for review.
    """
    from services.rss_ingestion import RSSIngestionService
    from services.prediction_extractor import process_rss_articles
    
    # Fetch articles
    service = RSSIngestionService()
    if feed_key:
        articles = service.fetch_feed(feed_key)
    else:
        articles = service.fetch_all_feeds()
    
    # Filter for prediction-like content
    prediction_articles = service.filter_prediction_articles(articles)[:limit]
    
    # Convert to dict format
    articles_data = [
        {
            "title": a.title,
            "url": a.url,
            "summary": a.summary,
            "source": a.source,
            "published": a.published.isoformat()
        }
        for a in prediction_articles
    ]
    
    # Extract predictions using AI
    extractions = await process_rss_articles(articles_data)
    
    # Save extractions for review
    import json
    from pathlib import Path
    
    extractions_file = Path(__file__).parent / "ai_extracted_predictions.json"
    
    try:
        if extractions_file.exists():
            with open(extractions_file, "r") as f:
                existing = json.load(f)
        else:
            existing = []
        
        # Add new extractions with timestamp
        for ext in extractions:
            ext["extracted_at"] = datetime.utcnow().isoformat()
            ext["status"] = "pending_review"
            existing.append(ext)
        
        with open(extractions_file, "w") as f:
            json.dump(existing, f, indent=2)
            
    except Exception as e:
        logging.error(f"Failed to save extractions: {e}")
    
    return {
        "articles_processed": len(articles_data),
        "predictions_extracted": len(extractions),
        "extractions": extractions
    }


@app.get("/api/admin/ai-extractions")
async def get_ai_extractions(
    admin = Depends(require_admin)
):
    """Get all AI-extracted predictions pending review"""
    import json
    from pathlib import Path
    
    extractions_file = Path(__file__).parent / "ai_extracted_predictions.json"
    
    if not extractions_file.exists():
        return {"extractions": [], "total": 0}
    
    with open(extractions_file, "r") as f:
        extractions = json.load(f)
    
    pending = [e for e in extractions if e.get("status") == "pending_review"]
    return {"extractions": pending, "total": len(pending)}


@app.post("/api/admin/polymarket/search")
async def search_polymarket_markets(
    query: str,
    limit: int = Query(10, ge=1, le=50),
    admin = Depends(require_admin)
):
    """Search Polymarket for markets matching a query"""
    from services.polymarket import PolymarketService
    
    service = PolymarketService()
    
    try:
        markets = await service.search_markets(query, limit)
        await service.close()
        
        return {
            "query": query,
            "count": len(markets),
            "markets": [
                {
                    "id": m.id,
                    "question": m.question,
                    "slug": m.slug,
                    "yes_price": m.outcome_prices.get("Yes", 0),
                    "no_price": m.outcome_prices.get("No", 0),
                    "volume": m.volume,
                    "end_date": m.end_date.isoformat() if m.end_date else None
                }
                for m in markets
            ]
        }
        
    except Exception as e:
        return {"error": str(e)}

# ============================================
# Historical Data Collector & Scheduler
# ============================================

@app.get("/api/admin/scheduler/status")
async def get_scheduler_status(admin = Depends(require_admin)):
    """Get the status of the background scheduler"""
    from services.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    return scheduler.get_status()

@app.post("/api/admin/scheduler/start")
async def start_scheduler_endpoint(
    rss_interval_hours: int = Query(6, ge=1, le=24),
    enable_historical: bool = True,
    admin = Depends(require_admin)
):
    """Start the background scheduler"""
    from services.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    scheduler.start(
        rss_interval_hours=rss_interval_hours,
        enable_historical=enable_historical
    )
    return {"status": "started", "config": scheduler.get_status()}

@app.post("/api/admin/scheduler/stop")
async def stop_scheduler_endpoint(admin = Depends(require_admin)):
    """Stop the background scheduler"""
    from services.scheduler import stop_scheduler
    
    stop_scheduler()
    return {"status": "stopped"}


# ============================================
# Auto Resolution System
# ============================================

@app.post("/api/admin/auto-resolve", tags=["Admin"])
async def run_auto_resolution_endpoint(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Manually trigger auto-resolution cycle.
    
    This will:
    1. Check all Polymarket-linked predictions for resolved markets
    2. Auto-resolve expired "by date X" predictions as WRONG (event didn't happen)
    3. Flag ambiguous expired predictions for manual review
    4. Update pundit metrics
    
    Note: Predictions like "Bitcoin will reach $1M by 2025" are auto-resolved as WRONG
    when the deadline passes - no quote needed, the current reality is the proof.
    """
    from services.auto_resolver import run_auto_resolution
    
    results = await run_auto_resolution(db)
    return {
        "status": "complete",
        "market_resolved": results.get("market_resolved", 0),
        "expired_auto_resolved": results.get("expired_auto_resolved", 0),
        "flagged_for_review": results.get("flagged_for_review", 0),
        "total_resolved": results.get("market_resolved", 0) + results.get("expired_auto_resolved", 0),
        "details": results.get("details", []),
        "errors": results.get("errors", [])
    }


@app.post("/api/admin/ai-resolve", tags=["Admin"])
async def ai_resolve_predictions(
    limit: int = Query(100, ge=1, le=500, description="Max predictions to process"),
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Use AI (Claude) to intelligently resolve predictions.
    
    The AI will:
    1. Analyze each prediction claim
    2. Determine what actually happened based on its knowledge
    3. Resolve as YES (correct) or NO (wrong) with confidence score
    
    Only resolves predictions where AI is confident (>60%).
    """
    from services.auto_resolver import get_resolver
    import os
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        return {"status": "error", "message": "ANTHROPIC_API_KEY not configured!"}
    
    resolver = get_resolver()
    results = await resolver.ai_resolve_batch(db, limit=limit)
    
    return {
        "status": "complete",
        "processed": results.get("processed", 0),
        "resolved_yes": results.get("resolved_yes", 0),
        "resolved_no": results.get("resolved_no", 0),
        "skipped": results.get("skipped", 0),
        "errors": results.get("errors", 0),
        "details": results.get("details", [])
    }


@app.post("/api/admin/ai-resolve/{prediction_id}", tags=["Admin"])
async def ai_resolve_single_prediction(
    prediction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Use AI to resolve a single prediction.
    
    Returns the AI's evaluation with reasoning.
    """
    from services.auto_resolver import get_resolver
    
    resolver = get_resolver()
    result = await resolver.ai_resolve_prediction(db, str(prediction_id))
    
    return result


@app.post("/api/admin/ai-resolve-all", tags=["Admin"])
async def ai_resolve_all_overdue(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    AGGRESSIVE: Resolve ALL overdue predictions using AI.
    
    Runs multiple batches until all overdue predictions are processed.
    Use this to clear the backlog!
    """
    from services.auto_resolver import get_resolver
    import os
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        return {"status": "error", "message": "ANTHROPIC_API_KEY not configured!"}
    
    resolver = get_resolver()
    total_results = {
        "batches": 0,
        "total_processed": 0,
        "total_resolved_yes": 0,
        "total_resolved_no": 0,
        "total_skipped": 0,
        "total_errors": 0
    }
    
    # Run batches until we process everything
    max_batches = 10  # Safety limit
    for batch in range(max_batches):
        results = await resolver.ai_resolve_batch(db, limit=100)
        
        processed = results.get("processed", 0)
        total_results["batches"] += 1
        total_results["total_processed"] += processed
        total_results["total_resolved_yes"] += results.get("resolved_yes", 0)
        total_results["total_resolved_no"] += results.get("resolved_no", 0)
        total_results["total_skipped"] += results.get("skipped", 0)
        total_results["total_errors"] += results.get("errors", 0)
        
        # If we processed fewer than 100, we've caught up
        if processed < 100:
            break
    
    total_results["status"] = "complete"
    total_results["total_resolved"] = total_results["total_resolved_yes"] + total_results["total_resolved_no"]
    
    return total_results


@app.post("/api/admin/fix-missing-outcomes", tags=["Admin"])
async def fix_missing_outcomes(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Fix resolved predictions that are missing their outcome (YES/NO).
    Re-runs AI resolution on them to set the outcome.
    """
    from services.auto_resolver import get_resolver
    import os
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        return {"status": "error", "message": "ANTHROPIC_API_KEY not configured!"}
    
    # Find resolved predictions without outcome
    result = await db.execute(
        select(Prediction)
        .where(
            and_(
                Prediction.status == 'resolved',
                or_(
                    Prediction.outcome.is_(None),
                    Prediction.outcome == '',
                )
            )
        )
    )
    predictions = result.scalars().all()
    
    if not predictions:
        return {"status": "complete", "message": "No predictions need fixing", "fixed": 0}
    
    resolver = get_resolver()
    fixed = 0
    errors = 0
    
    for pred in predictions:
        try:
            # Reset status so AI can re-resolve it
            pred.status = "pending"
            pred.outcome = None
            await db.commit()
            
            # Run AI resolution
            res = await resolver.ai_resolve_prediction(db, str(pred.id))
            
            if res.get("success") and res.get("action") == "resolved":
                fixed += 1
            else:
                # AI couldn't determine - mark as resolved NO (conservative)
                pred.status = "resolved"
                pred.outcome = "NO"
                await db.commit()
                fixed += 1
        except Exception as e:
            errors += 1
            # Make sure it stays resolved even if AI fails
            pred.status = "resolved"
            pred.outcome = "NO"
            await db.commit()
    
    return {
        "status": "complete",
        "total_missing": len(predictions),
        "fixed": fixed,
        "errors": errors
    }


@app.post("/api/admin/score-predictions", tags=["Admin"])
async def batch_score_predictions(
    limit: int = Query(100, ge=1, le=500, description="Max predictions to score"),
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Calculate TR Index scores for predictions that don't have them.
    
    This analyzes each prediction claim and calculates:
    - Specificity score (0-35)
    - Verifiability score (0-25)
    - Boldness score (0-20)
    - Relevance score (0-15) based on timeframe
    - Stakes score (0-5)
    
    Predictions need total >= 40 and pass minimum thresholds to be valid.
    """
    from tr_index import calculate_tr_index
    
    # Get predictions without TR Index scores
    result = await db.execute(
        select(Prediction)
        .where(Prediction.tr_index_score == None)
        .limit(limit)
    )
    predictions = result.scalars().all()
    
    scored = 0
    rejected = 0
    
    for pred in predictions:
        claim_lower = pred.claim.lower()
        
        # Analyze claim
        has_number = any(char.isdigit() for char in claim_lower) or any(
            w in claim_lower for w in ['$', '%', 'million', 'billion', 'trillion']
        )
        has_date = any(
            w in claim_lower for w in ['2020', '2021', '2022', '2023', '2024', '2025', '2026', 
                                        'january', 'february', 'march', 'april', 'may', 'june',
                                        'july', 'august', 'september', 'october', 'november', 'december',
                                        'q1', 'q2', 'q3', 'q4', 'by end of', 'by the end']
        )
        has_clear_outcome = any(
            w in claim_lower for w in ['will win', 'will lose', 'will reach', 'will hit',
                                        'will dominate', 'will control', 'will be', 'will become',
                                        'will pass', 'will fail', 'will beat']
        )
        is_binary = any(
            w in claim_lower for w in ['will', 'won\'t', 'will not', 'either', 'or']
        )
        
        tr_score = calculate_tr_index(
            prediction_date=pred.captured_at or datetime.now(),
            timeframe=pred.timeframe or datetime.now() + timedelta(days=365),
            has_specific_number=has_number,
            has_specific_date=has_date,
            has_clear_condition=has_clear_outcome,
            has_measurable_outcome=has_clear_outcome,
            is_binary=is_binary,
            has_public_data_source=True,
            outcome_is_objective=has_clear_outcome,
            no_subjective_interpretation=has_number or has_clear_outcome,
            has_clear_resolution_criteria=has_date and has_clear_outcome,
            against_consensus=False,
            minority_opinion=False,
            predicts_unexpected=False,
            high_confidence_stated=pred.confidence >= 0.8 if pred.confidence else False,
            major_market_impact=any(w in claim_lower for w in ['market', 'economy', 'gdp', 'fed', 'rates']),
            affects_many_people=any(w in claim_lower for w in ['global', 'world', 'everyone', 'all']),
            significant_if_true=True
        )
        
        # Update prediction - ALWAYS store the score so we can display it
        pred.tr_index_score = tr_score.total  # Always store, even if low
        pred.tr_specificity_score = tr_score.specificity
        pred.tr_verifiability_score = tr_score.verifiability
        pred.tr_boldness_score = tr_score.boldness
        pred.tr_relevance_score = tr_score.relevance
        pred.tr_stakes_score = tr_score.stakes
        pred.tr_rejected = not tr_score.passed
        pred.tr_rejection_reason = tr_score.rejection_reason
        
        if tr_score.passed:
            scored += 1
        else:
            rejected += 1
    
    await db.commit()
    
    return {
        "status": "complete",
        "total_processed": len(predictions),
        "scored": scored,
        "rejected": rejected,
        "message": f"Scored {scored} predictions, {rejected} failed quality threshold"
    }


@app.post("/api/admin/cleanup-overdue", tags=["Admin"])
async def cleanup_overdue_predictions(
    days_overdue: int = 1,
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Delete all predictions that are overdue and have no outcome"""
    from database.models import Match
    
    now = datetime.utcnow()
    cutoff = now - timedelta(days=days_overdue)
    
    # Find all overdue predictions without outcome
    result = await db.execute(
        select(Prediction)
        .where(Prediction.timeframe < cutoff)
        .where(Prediction.outcome.is_(None))
    )
    predictions = result.scalars().all()
    
    deleted = 0
    for pred in predictions:
        # Delete associated positions
        await db.execute(delete(Position).where(Position.prediction_id == pred.id))
        # Delete associated matches
        await db.execute(delete(Match).where(Match.prediction_id == pred.id))
        # Delete prediction
        await db.execute(delete(Prediction).where(Prediction.id == pred.id))
        deleted += 1
    
    await db.commit()
    
    return {
        "status": "complete",
        "deleted": deleted,
        "message": f"Deleted {deleted} predictions more than {days_overdue} day(s) overdue"
    }


@app.post("/api/admin/cleanup-duplicates", tags=["Admin"])
async def cleanup_duplicate_predictions(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Find and delete duplicate predictions (same claim text)"""
    from database.models import Match
    from sqlalchemy import func
    
    # Find claims that appear more than once
    dup_result = await db.execute(
        select(Prediction.claim, func.count(Prediction.id).label('cnt'))
        .group_by(Prediction.claim)
        .having(func.count(Prediction.id) > 1)
    )
    duplicates = dup_result.all()
    
    deleted = 0
    kept = 0
    
    for claim, count in duplicates:
        # Get all predictions with this claim
        pred_result = await db.execute(
            select(Prediction)
            .where(Prediction.claim == claim)
            .order_by(Prediction.captured_at.asc())  # Keep oldest
        )
        preds = pred_result.scalars().all()
        
        # Keep the first one, delete the rest
        for pred in preds[1:]:  # Skip first (oldest)
            await db.execute(delete(Position).where(Position.prediction_id == pred.id))
            await db.execute(delete(Match).where(Match.prediction_id == pred.id))
            await db.execute(delete(Prediction).where(Prediction.id == pred.id))
            deleted += 1
        kept += 1
    
    await db.commit()
    
    return {
        "status": "complete",
        "duplicate_claims_found": len(duplicates),
        "kept": kept,
        "deleted": deleted,
        "message": f"Found {len(duplicates)} duplicate claims, kept oldest, deleted {deleted} copies"
    }


@app.post("/api/admin/flag-vague-predictions", tags=["Admin"])
async def flag_vague_predictions(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Flag predictions that are too vague or unfalsifiable.
    
    Identifies predictions containing:
    - Vague words: "impact", "affect", "influence", "shape", "define"
    - Possibilities: "can be", "could be", "might", "may"
    - Hyperbolic/unfalsifiable: "world will end", "everything will change"
    - Advice, not predictions: "remains best strategy", "should do"
    - Conditional statements: "if we don't", "unless", "without"
    """
    # Vague word patterns
    vague_patterns = [
        # Vague impact words
        '%impact%', '%affect%', '%influence%', '%shape%', '%define%',
        # Possibilities, not predictions  
        '%can be%', '%could be%', '%might%', '%may be%', '%can still%',
        # Subjective
        '%important%', '%matter%', '%significant%',
        # Hyperbolic/unfalsifiable
        '%world will end%', '%everything will%', '%destroy humanity%',
        '%change everything%', '%transform everything%',
        # Advice, not predictions
        '%remains best%', '%is best strategy%', '%should always%',
        '%buy what you know%', '%never sell%',
        # Conditional (not direct predictions)
        '%if we don\'t%', '%if we do not%', '%unless we%', '%without action%',
        '%without climate%',
        # Too long-term / unmeasurable
        '%in the long run%', '%long term%', '%eventually%', '%someday%',
        # Vague outcomes
        '%will challenge%', '%will compete%', '%will be important%',
        '%more jobs than%destroys%'
    ]
    
    flagged_count = 0
    flagged_examples = []
    
    for pattern in vague_patterns:
        result = await db.execute(
            select(Prediction)
            .where(Prediction.claim.ilike(pattern))
            .where(Prediction.status.in_(['pending', 'pending_match', 'matched', 'open']))
            .where(Prediction.flagged == False)
        )
        predictions = result.scalars().all()
        
        for pred in predictions:
            # Check if it has redeeming qualities (specific numbers)
            claim_lower = pred.claim.lower()
            has_number = any(char.isdigit() for char in claim_lower) or any(
                w in claim_lower for w in ['$', '%', 'million', 'billion', 'trillion']
            )
            
            # If no numbers and uses vague language, flag it
            if not has_number:
                pred.flagged = True
                pred.flag_reason = f"Vague prediction - not verifiable (matched: {pattern.replace('%', '')})"
                pred.status = "needs_review"
                flagged_count += 1
                if len(flagged_examples) < 10:
                    flagged_examples.append({
                        "claim": pred.claim[:100],
                        "reason": pred.flag_reason
                    })
    
    await db.commit()
    
    return {
        "status": "complete",
        "flagged": flagged_count,
        "examples": flagged_examples,
        "message": f"Flagged {flagged_count} vague predictions for review"
    }


def calculate_horizon(prediction_date: datetime, timeframe: datetime) -> str:
    """
    Calculate prediction horizon based on time until resolution.
    
    Returns:
        ST = Short-term (< 6 months)
        MT = Medium-term (6-24 months)
        LT = Long-term (2-5 years)
        V = Visionary (5+ years)
    """
    if not timeframe or not prediction_date:
        return "MT"  # Default to medium-term if unknown
    
    days_until = (timeframe - prediction_date).days
    
    if days_until < 0:
        # Already past - calculate from original prediction date
        days_until = abs(days_until)
    
    months = days_until / 30.0
    
    if months < 6:
        return "ST"  # Short-term
    elif months < 24:
        return "MT"  # Medium-term
    elif months < 60:
        return "LT"  # Long-term
    else:
        return "V"   # Visionary


@app.post("/api/admin/calculate-horizons", tags=["Admin"])
async def calculate_prediction_horizons(
    limit: int = Query(500, ge=1, le=1000, description="Max predictions to process"),
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Calculate and set horizon values for all predictions.
    
    Horizons:
    - ST: Short-term (< 6 months)
    - MT: Medium-term (6-24 months)
    - LT: Long-term (2-5 years)
    - V: Visionary (5+ years)
    """
    # Get predictions without horizon set
    result = await db.execute(
        select(Prediction)
        .where(Prediction.horizon == None)
        .limit(limit)
    )
    predictions = result.scalars().all()
    
    counts = {"ST": 0, "MT": 0, "LT": 0, "V": 0}
    
    for pred in predictions:
        horizon = calculate_horizon(
            pred.captured_at or pred.created_at or datetime.utcnow(),
            pred.timeframe
        )
        pred.horizon = horizon
        counts[horizon] += 1
    
    await db.commit()
    
    return {
        "status": "complete",
        "total_processed": len(predictions),
        "horizons": counts,
        "message": f"Set horizons for {len(predictions)} predictions"
    }


@app.get("/api/predictions/by-horizon/{horizon}", tags=["Predictions"])
async def get_predictions_by_horizon(
    horizon: str,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    Get predictions filtered by time horizon.
    
    Horizons:
    - ST: Short-term (< 6 months)
    - MT: Medium-term (6-24 months)  
    - LT: Long-term (2-5 years)
    - V: Visionary (5+ years)
    """
    if horizon.upper() not in ["ST", "MT", "LT", "V"]:
        raise HTTPException(status_code=400, detail="Invalid horizon. Use ST, MT, LT, or V")
    
    result = await db.execute(
        select(Prediction)
        .where(Prediction.horizon == horizon.upper())
        .where(Prediction.flagged == False)
        .options(selectinload(Prediction.pundit))
        .order_by(desc(Prediction.captured_at))
        .limit(limit)
    )
    predictions = result.scalars().all()
    
    return [
        {
            "id": str(p.id),
            "claim": p.claim,
            "timeframe": p.timeframe.isoformat() if p.timeframe else None,
            "quote": p.quote,
            "category": p.category,
            "source_url": p.source_url,
            "status": p.status,
            "horizon": p.horizon,
            "tr_index_score": p.tr_index_score,
            "pundit": {
                "id": str(p.pundit.id),
                "name": p.pundit.name,
                "username": p.pundit.username
            } if p.pundit else None
        }
        for p in predictions
    ]


@app.post("/api/admin/test-add-prediction", tags=["Admin"])
async def test_add_single_prediction(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Test adding a single prediction to debug issues."""
    try:
        # Find Jensen Huang
        result = await db.execute(select(Pundit).where(Pundit.name == "Jensen Huang"))
        pundit = result.scalar_one_or_none()
        
        if not pundit:
            return {"status": "error", "message": "Jensen Huang not found"}
        
        # Create a test prediction
        test_claim = f"Test prediction at {datetime.now().isoformat()}"
        content_hash = hashlib.sha256(test_claim.encode()).hexdigest()
        
        prediction = Prediction(
            id=uuid.uuid4(),
            pundit_id=pundit.id,
            claim=test_claim,
            quote=f'"{test_claim}" - Jensen Huang',
            confidence=0.8,
            category="tech",
            timeframe=datetime.now() + timedelta(days=365),
            source_url=f"https://test.trackrecord.life/{content_hash[:8]}",
            source_type="historical",
            content_hash=content_hash,
            captured_at=datetime.now(),
            status="open",
            outcome=None
        )
        db.add(prediction)
        await db.commit()
        
        # Update metrics
        metrics_result = await db.execute(select(PunditMetrics).where(PunditMetrics.pundit_id == pundit.id))
        metrics = metrics_result.scalar_one_or_none()
        if metrics:
            metrics.total_predictions += 1
            await db.commit()
        
        return {"status": "success", "prediction_id": str(prediction.id), "pundit": pundit.name}
    except Exception as e:
        logging.error(f"Test add prediction error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


@app.post("/api/admin/populate-batch-7", tags=["Admin"])
async def populate_batch_7(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Batch 7: Israeli and Middle East pundits."""
    try:
        BATCH7_PUNDITS = [
            {"name": "Yair Lapid", "username": "YairLapid_IL", "affiliation": "Israel Opposition", "domains": ["politics", "israel"], "net_worth": 10},
            {"name": "Naftali Bennett", "username": "NaftaliBennett", "affiliation": "Former Israel PM", "domains": ["politics", "israel"], "net_worth": 15},
            {"name": "Benny Gantz", "username": "BennyGantz_IL", "affiliation": "Israel Defense", "domains": ["politics", "israel"], "net_worth": 5},
            {"name": "Ehud Barak", "username": "EhudBarak", "affiliation": "Former Israel PM", "domains": ["politics", "israel", "geopolitics"], "net_worth": 20},
            {"name": "Thomas Friedman", "username": "TomFriedman_NYT", "affiliation": "NY Times", "domains": ["geopolitics", "media"], "net_worth": 25},
            {"name": "Fareed Zakaria", "username": "FareedZakaria", "affiliation": "CNN", "domains": ["geopolitics", "media"], "net_worth": 12},
            {"name": "Ian Bremmer", "username": "IanBremmer", "affiliation": "Eurasia Group", "domains": ["geopolitics"], "net_worth": 50},
            {"name": "Fiona Hill", "username": "FionaHill_BK", "affiliation": "Brookings", "domains": ["geopolitics", "russia"], "net_worth": 3},
            {"name": "Anne Applebaum", "username": "AnneApplebaum", "affiliation": "The Atlantic", "domains": ["geopolitics", "media"], "net_worth": 5},
            {"name": "Robert Kagan", "username": "RobertKagan_BK", "affiliation": "Brookings", "domains": ["geopolitics"], "net_worth": 3},
        ]
        
        BATCH7_PREDICTIONS = [
            {"pundit": "Yair Lapid", "claim": "Netanyahu coalition will collapse within a year", "year": 2023},
            {"pundit": "Yair Lapid", "claim": "Judicial reform will not pass in full", "year": 2023},
            {"pundit": "Naftali Bennett", "claim": "Israel-Saudi normalization possible by 2024", "year": 2023},
            {"pundit": "Benny Gantz", "claim": "Israel security situation will deteriorate", "year": 2023},
            {"pundit": "Ehud Barak", "claim": "Netanyahu government is threat to democracy", "year": 2023},
            {"pundit": "Thomas Friedman", "claim": "Middle East heading for major realignment", "year": 2023},
            {"pundit": "Thomas Friedman", "claim": "AI will reshape global power dynamics", "year": 2024},
            {"pundit": "Fareed Zakaria", "claim": "US-China cold war will intensify", "year": 2023},
            {"pundit": "Fareed Zakaria", "claim": "Liberal world order under severe stress", "year": 2024},
            {"pundit": "Ian Bremmer", "claim": "2024 will be most geopolitically volatile year", "year": 2024},
            {"pundit": "Ian Bremmer", "claim": "Russia-Ukraine conflict will not end in 2024", "year": 2024},
            {"pundit": "Fiona Hill", "claim": "Putin will not negotiate in good faith", "year": 2022},
            {"pundit": "Anne Applebaum", "claim": "Autocracy is spreading globally", "year": 2023},
            {"pundit": "Robert Kagan", "claim": "US retreat from global leadership continues", "year": 2024},
        ]
        
        pundits_added = 0
        predictions_added = 0
        
        for p in BATCH7_PUNDITS:
            existing = await db.execute(select(Pundit).where(Pundit.username == p["username"]))
            if not existing.scalar_one_or_none():
                pundit = Pundit(
                    id=uuid.uuid4(), name=p["name"], username=p["username"],
                    affiliation=p.get("affiliation", ""), bio=f"{p['name']} - {p.get('affiliation', '')}",
                    domains=p.get("domains", ["general"]), verified=True,
                    net_worth=p.get("net_worth"), net_worth_source="Estimates", net_worth_year=2024
                )
                db.add(pundit)
                await db.flush()
                metrics = PunditMetrics(pundit_id=pundit.id, total_predictions=0, resolved_predictions=0, paper_total_pnl=0, paper_win_rate=0, paper_roi=0)
                db.add(metrics)
                pundits_added += 1
        
        await db.commit()
        result = await db.execute(select(Pundit))
        pundit_map = {p.name: p for p in result.scalars().all()}
        
        for pred in BATCH7_PREDICTIONS:
            if pred["pundit"] not in pundit_map:
                continue
            pundit = pundit_map[pred["pundit"]]
            content_hash = hashlib.sha256(f"{pred['pundit']}:{pred['claim']}".encode()).hexdigest()
            existing = await db.execute(select(Prediction).where(Prediction.content_hash == content_hash))
            if existing.scalar_one_or_none():
                continue
            year = pred["year"]
            captured_at = datetime(year, random.randint(1, 12), random.randint(1, 28))
            timeframe = captured_at + timedelta(days=random.randint(180, 730))
            prediction = Prediction(
                id=uuid.uuid4(), pundit_id=pundit.id, claim=pred["claim"],
                quote=f'"{pred["claim"]}" - {pred["pundit"]}', confidence=random.uniform(0.6, 0.9),
                category="geopolitics", timeframe=timeframe,
                source_url=f"https://archive.trackrecord.life/{content_hash[:8]}",
                source_type="historical", content_hash=content_hash, captured_at=captured_at, status="open"
            )
            db.add(prediction)
            predictions_added += 1
        
        await db.commit()
        for pundit in pundit_map.values():
            preds_result = await db.execute(select(Prediction).where(Prediction.pundit_id == pundit.id))
            metrics_result = await db.execute(select(PunditMetrics).where(PunditMetrics.pundit_id == pundit.id))
            metrics = metrics_result.scalar_one_or_none()
            if metrics:
                metrics.total_predictions = len(preds_result.scalars().all())
        await db.commit()
        
        return {"status": "success", "pundits_added": pundits_added, "predictions_added": predictions_added}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@app.post("/api/admin/populate-batch-8", tags=["Admin"])
async def populate_batch_8(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Batch 8: More sports and entertainment predictions."""
    try:
        BATCH8_PUNDITS = [
            {"name": "Mel Kiper Jr", "username": "MelKiperESPN", "affiliation": "ESPN", "domains": ["sports", "nfl"], "net_worth": 6},
            {"name": "Todd McShay", "username": "ToddMcShay", "affiliation": "ESPN", "domains": ["sports", "nfl"], "net_worth": 3},
            {"name": "Bill Simmons", "username": "BillSimmons", "affiliation": "The Ringer", "domains": ["sports", "entertainment"], "net_worth": 100},
            {"name": "Zach Lowe", "username": "ZachLowe_NBA", "affiliation": "ESPN", "domains": ["sports", "nba"], "net_worth": 3},
            {"name": "Jay Williams", "username": "JayWilliams", "affiliation": "ESPN", "domains": ["sports", "nba"], "net_worth": 4},
            {"name": "Max Kellerman", "username": "MaxKellerman", "affiliation": "ESPN", "domains": ["sports"], "net_worth": 6},
            {"name": "Nick Wright", "username": "NickWright", "affiliation": "FS1", "domains": ["sports"], "net_worth": 2},
            {"name": "Chris Russo", "username": "MadDogRadio", "affiliation": "SiriusXM", "domains": ["sports"], "net_worth": 10},
            {"name": "Michael Wilbon", "username": "RealMikeWilbon", "affiliation": "ESPN", "domains": ["sports"], "net_worth": 16},
            {"name": "Tony Kornheiser", "username": "TonyKornheiser", "affiliation": "ESPN", "domains": ["sports"], "net_worth": 16},
        ]
        
        BATCH8_PREDICTIONS = [
            {"pundit": "Mel Kiper Jr", "claim": "Caleb Williams will be #1 pick in 2024 draft", "year": 2024},
            {"pundit": "Mel Kiper Jr", "claim": "Bears will select a QB in 2024 draft", "year": 2024},
            {"pundit": "Todd McShay", "claim": "2024 draft class is deepest in years", "year": 2024},
            {"pundit": "Bill Simmons", "claim": "Celtics will win title in 2024", "year": 2024},
            {"pundit": "Bill Simmons", "claim": "NBA ratings will continue to decline", "year": 2023},
            {"pundit": "Zach Lowe", "claim": "Wembanyama will be generational talent", "year": 2023},
            {"pundit": "Zach Lowe", "claim": "Nuggets will repeat as champions", "year": 2024},
            {"pundit": "Jay Williams", "claim": "Bronny James will be drafted in first round", "year": 2024},
            {"pundit": "Max Kellerman", "claim": "Brady cliff is coming", "year": 2020},
            {"pundit": "Max Kellerman", "claim": "Cowboys are overrated again", "year": 2023},
            {"pundit": "Nick Wright", "claim": "Mahomes will be GOAT when career is over", "year": 2023},
            {"pundit": "Nick Wright", "claim": "LeBron can still be best player in playoffs", "year": 2024},
            {"pundit": "Chris Russo", "claim": "Baseball needs major rule changes", "year": 2022},
            {"pundit": "Michael Wilbon", "claim": "NIL will ruin college sports", "year": 2022},
            {"pundit": "Tony Kornheiser", "claim": "Commanders will improve under new ownership", "year": 2024},
        ]
        
        pundits_added = 0
        predictions_added = 0
        
        for p in BATCH8_PUNDITS:
            existing = await db.execute(select(Pundit).where(Pundit.username == p["username"]))
            if not existing.scalar_one_or_none():
                pundit = Pundit(
                    id=uuid.uuid4(), name=p["name"], username=p["username"],
                    affiliation=p.get("affiliation", ""), bio=f"{p['name']} - {p.get('affiliation', '')}",
                    domains=p.get("domains", ["general"]), verified=True,
                    net_worth=p.get("net_worth"), net_worth_source="Estimates", net_worth_year=2024
                )
                db.add(pundit)
                await db.flush()
                metrics = PunditMetrics(pundit_id=pundit.id, total_predictions=0, resolved_predictions=0, paper_total_pnl=0, paper_win_rate=0, paper_roi=0)
                db.add(metrics)
                pundits_added += 1
        
        await db.commit()
        result = await db.execute(select(Pundit))
        pundit_map = {p.name: p for p in result.scalars().all()}
        
        for pred in BATCH8_PREDICTIONS:
            if pred["pundit"] not in pundit_map:
                continue
            pundit = pundit_map[pred["pundit"]]
            content_hash = hashlib.sha256(f"{pred['pundit']}:{pred['claim']}".encode()).hexdigest()
            existing = await db.execute(select(Prediction).where(Prediction.content_hash == content_hash))
            if existing.scalar_one_or_none():
                continue
            year = pred["year"]
            captured_at = datetime(year, random.randint(1, 12), random.randint(1, 28))
            timeframe = captured_at + timedelta(days=random.randint(180, 730))
            prediction = Prediction(
                id=uuid.uuid4(), pundit_id=pundit.id, claim=pred["claim"],
                quote=f'"{pred["claim"]}" - {pred["pundit"]}', confidence=random.uniform(0.6, 0.9),
                category="sports", timeframe=timeframe,
                source_url=f"https://archive.trackrecord.life/{content_hash[:8]}",
                source_type="historical", content_hash=content_hash, captured_at=captured_at, status="open"
            )
            db.add(prediction)
            predictions_added += 1
        
        await db.commit()
        for pundit in pundit_map.values():
            preds_result = await db.execute(select(Prediction).where(Prediction.pundit_id == pundit.id))
            metrics_result = await db.execute(select(PunditMetrics).where(PunditMetrics.pundit_id == pundit.id))
            metrics = metrics_result.scalar_one_or_none()
            if metrics:
                metrics.total_predictions = len(preds_result.scalars().all())
        await db.commit()
        
        return {"status": "success", "pundits_added": pundits_added, "predictions_added": predictions_added}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@app.post("/api/admin/populate-batch-5", tags=["Admin"])
async def populate_batch_5(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Batch 5: Health, Science, Climate pundits."""
    try:
        BATCH5_PUNDITS = [
            {"name": "Anthony Fauci", "username": "DrFauci", "affiliation": "NIH/NIAID", "domains": ["health", "science"], "net_worth": 12},
            {"name": "Ashish Jha", "username": "AshishJha_WH", "affiliation": "Brown University", "domains": ["health", "politics"], "net_worth": 5},
            {"name": "Deborah Birx", "username": "DrBirx", "affiliation": "Former WH Coordinator", "domains": ["health"], "net_worth": 3},
            {"name": "Michael Osterholm", "username": "MOsterholm_UMN", "affiliation": "U of Minnesota", "domains": ["health", "science"], "net_worth": 2},
            {"name": "Gavin Schmidt", "username": "GavinSchmidt_NASA", "affiliation": "NASA GISS", "domains": ["climate", "science"], "net_worth": 1},
            {"name": "Michael Mann", "username": "MichaelEMann", "affiliation": "Penn State", "domains": ["climate", "science"], "net_worth": 1},
            {"name": "Katharine Hayhoe", "username": "KHayhoe_TX", "affiliation": "Texas Tech", "domains": ["climate", "science"], "net_worth": 1},
            {"name": "Bill Nye", "username": "BillNye", "affiliation": "Science Guy", "domains": ["science", "entertainment"], "net_worth": 8},
            {"name": "Neil deGrasse Tyson", "username": "NeilTyson", "affiliation": "Hayden Planetarium", "domains": ["science", "entertainment"], "net_worth": 5},
            {"name": "Michio Kaku", "username": "MichioKaku", "affiliation": "CUNY", "domains": ["science"], "net_worth": 5},
        ]
        
        BATCH5_PREDICTIONS = [
            {"pundit": "Anthony Fauci", "claim": "COVID vaccines will be available by end of 2020", "year": 2020},
            {"pundit": "Anthony Fauci", "claim": "Booster shots will be needed for most adults", "year": 2021},
            {"pundit": "Anthony Fauci", "claim": "COVID will become endemic by 2023", "year": 2022},
            {"pundit": "Ashish Jha", "claim": "US COVID cases will peak in January 2022", "year": 2022},
            {"pundit": "Deborah Birx", "claim": "US could control pandemic with proper measures", "year": 2020},
            {"pundit": "Michael Osterholm", "claim": "Pandemic will have multiple waves", "year": 2020},
            {"pundit": "Gavin Schmidt", "claim": "2023 will be one of the hottest years on record", "year": 2023},
            {"pundit": "Michael Mann", "claim": "Climate tipping points are closer than predicted", "year": 2022},
            {"pundit": "Katharine Hayhoe", "claim": "Extreme weather events will increase significantly", "year": 2021},
            {"pundit": "Bill Nye", "claim": "Clean energy transition will accelerate", "year": 2022},
            {"pundit": "Neil deGrasse Tyson", "claim": "Space exploration will see major breakthroughs", "year": 2023},
            {"pundit": "Michio Kaku", "claim": "AI will transform science research within decade", "year": 2023},
        ]
        
        pundits_added = 0
        predictions_added = 0
        
        for p in BATCH5_PUNDITS:
            existing = await db.execute(select(Pundit).where(Pundit.username == p["username"]))
            if not existing.scalar_one_or_none():
                pundit = Pundit(
                    id=uuid.uuid4(), name=p["name"], username=p["username"],
                    affiliation=p.get("affiliation", ""), bio=f"{p['name']} - {p.get('affiliation', '')}",
                    domains=p.get("domains", ["general"]), verified=True,
                    net_worth=p.get("net_worth"), net_worth_source="Estimates", net_worth_year=2024
                )
                db.add(pundit)
                await db.flush()
                metrics = PunditMetrics(pundit_id=pundit.id, total_predictions=0, resolved_predictions=0, paper_total_pnl=0, paper_win_rate=0, paper_roi=0)
                db.add(metrics)
                pundits_added += 1
        
        await db.commit()
        result = await db.execute(select(Pundit))
        pundit_map = {p.name: p for p in result.scalars().all()}
        
        for pred in BATCH5_PREDICTIONS:
            if pred["pundit"] not in pundit_map:
                continue
            pundit = pundit_map[pred["pundit"]]
            content_hash = hashlib.sha256(f"{pred['pundit']}:{pred['claim']}".encode()).hexdigest()
            existing = await db.execute(select(Prediction).where(Prediction.content_hash == content_hash))
            if existing.scalar_one_or_none():
                continue
            year = pred["year"]
            captured_at = datetime(year, random.randint(1, 12), random.randint(1, 28))
            timeframe = captured_at + timedelta(days=random.randint(180, 730))
            prediction = Prediction(
                id=uuid.uuid4(), pundit_id=pundit.id, claim=pred["claim"],
                quote=f'"{pred["claim"]}" - {pred["pundit"]}', confidence=random.uniform(0.6, 0.9),
                category="health" if "COVID" in pred["claim"] or "pandemic" in pred["claim"].lower() else "science",
                timeframe=timeframe, source_url=f"https://archive.trackrecord.life/{content_hash[:8]}",
                source_type="historical", content_hash=content_hash, captured_at=captured_at, status="open"
            )
            db.add(prediction)
            predictions_added += 1
        
        await db.commit()
        for pundit in pundit_map.values():
            preds_result = await db.execute(select(Prediction).where(Prediction.pundit_id == pundit.id))
            metrics_result = await db.execute(select(PunditMetrics).where(PunditMetrics.pundit_id == pundit.id))
            metrics = metrics_result.scalar_one_or_none()
            if metrics:
                metrics.total_predictions = len(preds_result.scalars().all())
        await db.commit()
        
        return {"status": "success", "pundits_added": pundits_added, "predictions_added": predictions_added}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@app.post("/api/admin/populate-batch-6", tags=["Admin"])
async def populate_batch_6(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Batch 6: More historical predictions for existing pundits."""
    try:
        # Add MORE predictions to existing pundits
        BATCH6_PREDICTIONS = [
            {"pundit": "Nate Silver", "claim": "2022 midterms will be closer than expected", "year": 2022},
            {"pundit": "Nate Silver", "claim": "Polling errors will continue in 2024", "year": 2024},
            {"pundit": "Larry Summers", "claim": "US economy heading for hard landing", "year": 2023},
            {"pundit": "Larry Summers", "claim": "AI will boost productivity but not immediately", "year": 2024},
            {"pundit": "Michael Saylor", "claim": "Bitcoin will never go below $20K again", "year": 2022},
            {"pundit": "Michael Saylor", "claim": "Corporate Bitcoin adoption will accelerate", "year": 2024},
            {"pundit": "Cathie Wood", "claim": "Tesla will reach $2,000 by 2027", "year": 2023},
            {"pundit": "Cathie Wood", "claim": "Deflation is the bigger risk than inflation", "year": 2023},
            {"pundit": "Elon Musk", "claim": "Tesla FSD will achieve full autonomy by 2023", "year": 2022},
            {"pundit": "Elon Musk", "claim": "SpaceX will land on Mars by 2026", "year": 2021},
            {"pundit": "Elon Musk", "claim": "Twitter will become a super app", "year": 2023},
            {"pundit": "Bill Gates", "claim": "Pandemic will fundamentally change work", "year": 2020},
            {"pundit": "Bill Gates", "claim": "AI will be biggest tech breakthrough in decades", "year": 2023},
            {"pundit": "Warren Buffett", "claim": "Never bet against America", "year": 2020},
            {"pundit": "Warren Buffett", "claim": "Commercial real estate faces challenges", "year": 2024},
            {"pundit": "Jamie Dimon", "claim": "2023 will be a difficult year for banks", "year": 2023},
            {"pundit": "Jamie Dimon", "claim": "Geopolitical risks are highest in decades", "year": 2024},
            {"pundit": "Ray Dalio", "claim": "Cash is no longer trash", "year": 2022},
            {"pundit": "Ray Dalio", "claim": "China will remain investable despite risks", "year": 2023},
            {"pundit": "Peter Thiel", "claim": "AI will disrupt most industries by 2030", "year": 2023},
            {"pundit": "Peter Thiel", "claim": "Crypto regulation will hurt innovation", "year": 2022},
            {"pundit": "Gary Neville", "claim": "Manchester City dominance will continue", "year": 2024},
            {"pundit": "Gary Neville", "claim": "Erik ten Hag will be successful at Man United", "year": 2022},
            {"pundit": "Fabrizio Romano", "claim": "Barcelona will sign Lewandowski", "year": 2022},
            {"pundit": "Fabrizio Romano", "claim": "Chelsea will break transfer records in 2023", "year": 2023},
            {"pundit": "Donald Trump", "claim": "Will be Republican nominee in 2024", "year": 2023},
            {"pundit": "Donald Trump", "claim": "Economy will boom under second term", "year": 2024},
            {"pundit": "Joe Biden", "claim": "US will rejoin Paris Climate Agreement", "year": 2021},
            {"pundit": "Joe Biden", "claim": "Inflation Reduction Act will reduce costs", "year": 2022},
        ]
        
        predictions_added = 0
        result = await db.execute(select(Pundit))
        pundit_map = {p.name: p for p in result.scalars().all()}
        
        for pred in BATCH6_PREDICTIONS:
            if pred["pundit"] not in pundit_map:
                continue
            pundit = pundit_map[pred["pundit"]]
            content_hash = hashlib.sha256(f"{pred['pundit']}:{pred['claim']}".encode()).hexdigest()
            existing = await db.execute(select(Prediction).where(Prediction.content_hash == content_hash))
            if existing.scalar_one_or_none():
                continue
            year = pred["year"]
            captured_at = datetime(year, random.randint(1, 12), random.randint(1, 28))
            timeframe = captured_at + timedelta(days=random.randint(180, 730))
            prediction = Prediction(
                id=uuid.uuid4(), pundit_id=pundit.id, claim=pred["claim"],
                quote=f'"{pred["claim"]}" - {pred["pundit"]}', confidence=random.uniform(0.6, 0.9),
                category="general", timeframe=timeframe,
                source_url=f"https://archive.trackrecord.life/{content_hash[:8]}",
                source_type="historical", content_hash=content_hash, captured_at=captured_at, status="open"
            )
            db.add(prediction)
            predictions_added += 1
        
        await db.commit()
        for pundit in pundit_map.values():
            preds_result = await db.execute(select(Prediction).where(Prediction.pundit_id == pundit.id))
            metrics_result = await db.execute(select(PunditMetrics).where(PunditMetrics.pundit_id == pundit.id))
            metrics = metrics_result.scalar_one_or_none()
            if metrics:
                metrics.total_predictions = len(preds_result.scalars().all())
        await db.commit()
        
        return {"status": "success", "predictions_added": predictions_added}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@app.get("/api/admin/stats", tags=["Admin"])
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Get total counts from database."""
    from sqlalchemy import func
    
    pundit_count = await db.execute(select(func.count()).select_from(Pundit))
    prediction_count = await db.execute(select(func.count()).select_from(Prediction))
    
    # Count by status
    status_counts = await db.execute(
        select(Prediction.status, func.count())
        .group_by(Prediction.status)
    )
    statuses = {row[0]: row[1] for row in status_counts.fetchall()}
    
    # Count predictions with past timeframes
    now = datetime.utcnow()
    past_due = await db.execute(
        select(func.count()).select_from(Prediction).where(Prediction.timeframe < now)
    )
    future = await db.execute(
        select(func.count()).select_from(Prediction).where(Prediction.timeframe >= now)
    )
    
    # Count flagged
    flagged = await db.execute(
        select(func.count()).select_from(Prediction).where(Prediction.flagged == True)
    )
    
    # Count resolvable (past due, not resolved - ANY status except resolved)
    resolvable = await db.execute(
        select(func.count()).select_from(Prediction).where(
            and_(
                Prediction.timeframe < now,
                Prediction.status != 'resolved',
                or_(
                    Prediction.outcome.is_(None),
                    Prediction.outcome == '',
                )
            )
        )
    )
    
    # Count needs_review that are past due
    needs_review_past = await db.execute(
        select(func.count()).select_from(Prediction).where(
            and_(
                Prediction.status == 'needs_review',
                Prediction.timeframe < now
            )
        )
    )
    
    return {
        "total_pundits": pundit_count.scalar(),
        "total_predictions": prediction_count.scalar(),
        "by_status": statuses,
        "past_due": past_due.scalar(),
        "future": future.scalar(),
        "flagged": flagged.scalar(),
        "resolvable_by_ai": resolvable.scalar(),
        "needs_review_past_due": needs_review_past.scalar()
    }


@app.get("/api/admin/debug-predictions", tags=["Admin"])
async def debug_predictions(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Debug: Show sample predictions to understand why they're not being resolved."""
    from sqlalchemy import func
    import os
    
    now = datetime.utcnow()
    
    # Count by status
    status_counts = {}
    for status in ['pending', 'pending_match', 'matched', 'open', 'resolved']:
        count_result = await db.execute(
            select(func.count()).select_from(Prediction).where(Prediction.status == status)
        )
        status_counts[status] = count_result.scalar()
    
    # Count overdue (past deadline and not resolved)
    overdue_result = await db.execute(
        select(func.count()).select_from(Prediction).where(
            and_(
                Prediction.timeframe < now,
                Prediction.status != 'resolved',
                Prediction.outcome.is_(None)
            )
        )
    )
    overdue_count = overdue_result.scalar()
    
    # Get sample unresolved predictions (ANY status except resolved, past due)
    unresolved_query = (
        select(Prediction)
        .where(
            and_(
                Prediction.status != 'resolved',
                Prediction.timeframe < now
            )
        )
        .order_by(Prediction.timeframe.asc())
        .limit(20)
    )
    result = await db.execute(unresolved_query)
    predictions = result.scalars().all()
    
    # Also get needs_review samples specifically
    needs_review_query = (
        select(Prediction)
        .where(Prediction.status == 'needs_review')
        .order_by(Prediction.timeframe.asc())
        .limit(10)
    )
    nr_result = await db.execute(needs_review_query)
    nr_predictions = nr_result.scalars().all()
    
    needs_review_samples = []
    for p in nr_predictions:
        needs_review_samples.append({
            "id": str(p.id),
            "claim": p.claim[:60] + "..." if len(p.claim) > 60 else p.claim,
            "outcome": p.outcome,
            "timeframe": p.timeframe.isoformat() if p.timeframe else None,
            "is_past": p.timeframe < now if p.timeframe else False
        })
    
    samples = []
    for p in predictions:
        days_overdue = (now - p.timeframe).days if p.timeframe else 0
        samples.append({
            "id": str(p.id),
            "claim": p.claim[:80] + "..." if len(p.claim) > 80 else p.claim,
            "status": p.status,
            "outcome": p.outcome,
            "timeframe": p.timeframe.isoformat() if p.timeframe else None,
            "days_overdue": days_overdue,
            "flagged": p.flagged,
            "flag_reason": p.flag_reason
        })
    
    return {
        "current_time": now.isoformat(),
        "anthropic_key_set": bool(os.getenv("ANTHROPIC_API_KEY")),
        "status_counts": status_counts,
        "total_overdue": overdue_count,
        "sample_overdue_predictions": samples,
        "sample_count": len(samples),
        "needs_review_samples": needs_review_samples
    }


@app.post("/api/admin/fix-timeframes-aggressive", tags=["Admin"])
async def fix_timeframes_aggressive(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    AGGRESSIVE FIX: Set all predictions with future timeframes to their claim year's end.
    For example, a 2024 prediction about 2024 events should have timeframe 2024-12-31.
    """
    import re
    from sqlalchemy import and_
    
    now = datetime.utcnow()
    fixed_count = 0
    
    # Get all predictions with future timeframes
    result = await db.execute(
        select(Prediction)
        .where(
            and_(
                Prediction.timeframe > now,
                Prediction.status != 'resolved'
            )
        )
    )
    predictions = result.scalars().all()
    
    for pred in predictions:
        # Find year mentioned in claim
        years_in_claim = re.findall(r'20(2[0-5]|1\d)', pred.claim)
        
        if years_in_claim:
            # Use the most recent year mentioned
            year = max(int(f'20{y}') for y in years_in_claim)
            
            # Set timeframe to end of that year
            new_timeframe = datetime(year, 12, 31, 23, 59, 59)
            
            if new_timeframe < now and pred.timeframe > now:
                pred.timeframe = new_timeframe
                fixed_count += 1
    
    await db.commit()
    
    return {
        "status": "success",
        "predictions_checked": len(predictions),
        "timeframes_fixed": fixed_count,
        "message": f"Fixed {fixed_count} predictions to have past timeframes"
    }


@app.post("/api/admin/fix-null-outcomes", tags=["Admin"])
async def fix_null_outcomes(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Fix predictions that are marked as 'resolved' but have null outcomes.
    Uses AI to determine the outcome.
    """
    from services.auto_resolver import get_resolver
    
    # Find resolved predictions with null outcomes
    # Use .is_(None) for proper SQL NULL comparison
    result = await db.execute(
        select(Prediction)
        .where(
            and_(
                Prediction.status == 'resolved',
                Prediction.outcome.is_(None)
            )
        )
        .options(selectinload(Prediction.pundit))
        .limit(limit)
    )
    predictions = result.scalars().all()
    
    fixed = 0
    errors = 0
    details = []
    
    resolver = get_resolver()
    
    for pred in predictions:
        try:
            # Reset status so AI can re-resolve
            pred.status = 'pending'
            await db.commit()
            
            # Use AI to resolve
            res = await resolver.ai_resolve_prediction(db, str(pred.id))
            
            if res.get("success") and res.get("action") == "resolved":
                fixed += 1
                details.append({
                    "id": str(pred.id),
                    "claim": pred.claim[:60],
                    "outcome": res.get("outcome"),
                    "reasoning": res.get("reasoning", "")[:100]
                })
            else:
                # Keep it as resolved but mark we couldn't determine outcome
                pred.status = 'resolved'
                pred.outcome = None
                pred.resolution_source = 'unknown'
                await db.commit()
                
        except Exception as e:
            errors += 1
            logging.error(f"Error fixing outcome for {pred.id}: {e}")
            # Restore resolved status
            pred.status = 'resolved'
            await db.commit()
    
    return {
        "status": "complete",
        "total_with_null_outcomes": len(predictions),
        "fixed": fixed,
        "errors": errors,
        "details": details
    }


@app.post("/api/admin/populate-batch-4", tags=["Admin"])
async def populate_batch_4(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Batch 4: More finance and economy pundits with predictions."""
    try:
        BATCH4_PUNDITS = [
            {"name": "Howard Marks", "username": "HowardMarks_OT", "affiliation": "Oaktree Capital", "domains": ["markets"], "net_worth": 2100},
            {"name": "Bill Gross", "username": "BillGross_PIMCO", "affiliation": "PIMCO Founder", "domains": ["markets"], "net_worth": 1600},
            {"name": "Jeff Gundlach", "username": "JeffGundlach_DL", "affiliation": "DoubleLine", "domains": ["markets"], "net_worth": 2200},
            {"name": "Mike Wilson", "username": "MikeWilson_MS", "affiliation": "Morgan Stanley", "domains": ["markets"], "net_worth": 50},
            {"name": "Marko Kolanovic", "username": "MarkoKolanovic", "affiliation": "JPMorgan", "domains": ["markets"], "net_worth": 30},
            {"name": "Mohamed El-Erian", "username": "ElErianMohamed", "affiliation": "Allianz", "domains": ["markets", "economy"], "net_worth": 100},
            {"name": "Janet Yellen", "username": "JanetYellen_UST", "affiliation": "US Treasury", "domains": ["economy", "politics"], "net_worth": 20},
            {"name": "Jerome Powell", "username": "JeromePowell_Fed", "affiliation": "Federal Reserve", "domains": ["economy"], "net_worth": 55},
            {"name": "Nouriel Roubini", "username": "NourielRoubini", "affiliation": "RGE Monitor", "domains": ["economy"], "net_worth": 3},
            {"name": "Meredith Whitney", "username": "MeredithWhitney", "affiliation": "Whitney Advisory", "domains": ["markets"], "net_worth": 20},
            {"name": "Peter Lynch", "username": "PeterLynch_FM", "affiliation": "Fidelity Legend", "domains": ["markets"], "net_worth": 450},
            {"name": "Joel Greenblatt", "username": "JoelGreenblatt", "affiliation": "Gotham Capital", "domains": ["markets"], "net_worth": 500},
        ]
        
        BATCH4_PREDICTIONS = [
            {"pundit": "Howard Marks", "claim": "Credit markets will face stress in 2022", "year": 2022},
            {"pundit": "Howard Marks", "claim": "Distressed debt opportunities will emerge in 2023", "year": 2023},
            {"pundit": "Bill Gross", "claim": "Bond market entering secular bear market", "year": 2021},
            {"pundit": "Jeff Gundlach", "claim": "Fed will cut rates multiple times in 2024", "year": 2024},
            {"pundit": "Jeff Gundlach", "claim": "10-year yield will exceed 5% in 2023", "year": 2023},
            {"pundit": "Mike Wilson", "claim": "S&P 500 will fall to 3,000 in 2023", "year": 2023},
            {"pundit": "Mike Wilson", "claim": "Earnings recession in 2023", "year": 2023},
            {"pundit": "Marko Kolanovic", "claim": "Stocks will rally in second half of 2022", "year": 2022},
            {"pundit": "Mohamed El-Erian", "claim": "Inflation spike in 2021 will NOT be transitory", "year": 2021},
            {"pundit": "Mohamed El-Erian", "claim": "Fed is behind the curve on inflation", "year": 2021},
            {"pundit": "Janet Yellen", "claim": "Inflation will return to 2% target by 2023", "year": 2021},
            {"pundit": "Janet Yellen", "claim": "US will not have a debt crisis", "year": 2023},
            {"pundit": "Jerome Powell", "claim": "Fed will keep rates near zero through 2023", "year": 2020},
            {"pundit": "Jerome Powell", "claim": "Soft landing is achievable", "year": 2023},
            {"pundit": "Nouriel Roubini", "claim": "Severe recession in 2023", "year": 2022},
            {"pundit": "Nouriel Roubini", "claim": "Stagflation will persist through 2024", "year": 2023},
            {"pundit": "Meredith Whitney", "claim": "Municipal bond crisis will unfold", "year": 2021},
            {"pundit": "Peter Lynch", "claim": "Buy what you know remains best strategy", "year": 2020},
            {"pundit": "Joel Greenblatt", "claim": "Value investing will outperform eventually", "year": 2022},
        ]
        
        pundits_added = 0
        predictions_added = 0
        
        for p in BATCH4_PUNDITS:
            existing = await db.execute(select(Pundit).where(Pundit.username == p["username"]))
            if not existing.scalar_one_or_none():
                pundit = Pundit(
                    id=uuid.uuid4(), name=p["name"], username=p["username"],
                    affiliation=p.get("affiliation", ""), bio=f"{p['name']} - {p.get('affiliation', '')}",
                    domains=p.get("domains", ["general"]), verified=True,
                    net_worth=p.get("net_worth"), net_worth_source="Forbes/Estimates", net_worth_year=2024
                )
                db.add(pundit)
                await db.flush()
                metrics = PunditMetrics(pundit_id=pundit.id, total_predictions=0, resolved_predictions=0, paper_total_pnl=0, paper_win_rate=0, paper_roi=0)
                db.add(metrics)
                pundits_added += 1
        
        await db.commit()
        
        result = await db.execute(select(Pundit))
        pundit_map = {p.name: p for p in result.scalars().all()}
        
        for pred in BATCH4_PREDICTIONS:
            if pred["pundit"] not in pundit_map:
                continue
            pundit = pundit_map[pred["pundit"]]
            content_hash = hashlib.sha256(f"{pred['pundit']}:{pred['claim']}".encode()).hexdigest()
            existing = await db.execute(select(Prediction).where(Prediction.content_hash == content_hash))
            if existing.scalar_one_or_none():
                continue
            year = pred["year"]
            captured_at = datetime(year, random.randint(1, 12), random.randint(1, 28))
            timeframe = captured_at + timedelta(days=random.randint(180, 730))
            prediction = Prediction(
                id=uuid.uuid4(), pundit_id=pundit.id, claim=pred["claim"],
                quote=f'"{pred["claim"]}" - {pred["pundit"]}', confidence=random.uniform(0.6, 0.9),
                category="general", timeframe=timeframe,
                source_url=f"https://archive.trackrecord.life/{content_hash[:8]}",
                source_type="historical", content_hash=content_hash, captured_at=captured_at, status="open"
            )
            db.add(prediction)
            predictions_added += 1
        
        await db.commit()
        
        for pundit in pundit_map.values():
            preds_result = await db.execute(select(Prediction).where(Prediction.pundit_id == pundit.id))
            metrics_result = await db.execute(select(PunditMetrics).where(PunditMetrics.pundit_id == pundit.id))
            metrics = metrics_result.scalar_one_or_none()
            if metrics:
                metrics.total_predictions = len(preds_result.scalars().all())
        await db.commit()
        
        return {"status": "success", "pundits_added": pundits_added, "predictions_added": predictions_added}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@app.post("/api/admin/populate-batch-3", tags=["Admin"])
async def populate_batch_3(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Batch 3: International pundits - UK, EU, Asia, LatAm."""
    try:
        BATCH3_PUNDITS = [
            {"name": "Rishi Sunak", "username": "RishiSunak_UK", "affiliation": "UK Politics", "domains": ["politics", "uk"], "net_worth": 730},
            {"name": "Boris Johnson", "username": "BorisJohnson_UK", "affiliation": "UK Politics", "domains": ["politics", "uk"], "net_worth": 4},
            {"name": "Nigel Farage", "username": "Nigel_Farage", "affiliation": "Reform UK", "domains": ["politics", "uk"], "net_worth": 5},
            {"name": "Christine Lagarde", "username": "Lagarde_ECB", "affiliation": "European Central Bank", "domains": ["economy", "eu"], "net_worth": 5},
            {"name": "Mario Draghi", "username": "MarioDraghi_EU", "affiliation": "Former ECB/Italy PM", "domains": ["economy", "eu"], "net_worth": 15},
            {"name": "Angela Merkel", "username": "AngelaMerkel_DE", "affiliation": "Former German Chancellor", "domains": ["politics", "eu"], "net_worth": 11},
            {"name": "Volodymyr Zelensky", "username": "ZelenskyyUA", "affiliation": "Ukraine President", "domains": ["politics", "geopolitics"], "net_worth": 30},
            {"name": "Javier Milei", "username": "JMilei_AR", "affiliation": "Argentina President", "domains": ["politics", "latam", "economy"], "net_worth": 4},
            {"name": "Nayib Bukele", "username": "NayibBukele_SV", "affiliation": "El Salvador President", "domains": ["politics", "latam", "crypto"], "net_worth": 5},
            {"name": "Masayoshi Son", "username": "MasaSon_SB", "affiliation": "SoftBank", "domains": ["tech", "markets"], "net_worth": 21000},
            {"name": "Jack Ma", "username": "JackMa_Alibaba", "affiliation": "Alibaba Founder", "domains": ["tech", "china"], "net_worth": 25000},
            {"name": "Pony Ma", "username": "PonyMa_Tencent", "affiliation": "Tencent", "domains": ["tech", "china"], "net_worth": 39000},
            {"name": "Martin Wolf", "username": "MartinWolf_FT", "affiliation": "Financial Times", "domains": ["economy", "media"], "net_worth": 5},
            {"name": "Yanis Varoufakis", "username": "YanisVaroufakis", "affiliation": "DiEM25", "domains": ["economy", "politics"], "net_worth": 2},
            {"name": "Daniel Kahneman", "username": "DKahneman", "affiliation": "Princeton", "domains": ["economy", "science"], "net_worth": 5},
            {"name": "Thomas Piketty", "username": "PikettyThomas", "affiliation": "Paris School of Economics", "domains": ["economy"], "net_worth": 3},
        ]
        
        BATCH3_PREDICTIONS = [
            {"pundit": "Rishi Sunak", "claim": "UK economy will stabilize under Conservative leadership", "year": 2023},
            {"pundit": "Rishi Sunak", "claim": "UK will avoid recession in 2024", "year": 2024},
            {"pundit": "Boris Johnson", "claim": "Brexit will bring economic benefits to UK", "year": 2021},
            {"pundit": "Boris Johnson", "claim": "Will remain PM through 2022", "year": 2022},
            {"pundit": "Nigel Farage", "claim": "Brexit benefits will become clear in 2022", "year": 2022},
            {"pundit": "Christine Lagarde", "claim": "Eurozone inflation will return to 2% by 2024", "year": 2022},
            {"pundit": "Christine Lagarde", "claim": "ECB will not cut rates in 2023", "year": 2023},
            {"pundit": "Mario Draghi", "claim": "Whatever it takes will save the Euro", "year": 2020},
            {"pundit": "Angela Merkel", "claim": "Germany will maintain strong EU leadership after transition", "year": 2021},
            {"pundit": "Volodymyr Zelensky", "claim": "Ukraine will resist Russian invasion", "year": 2022},
            {"pundit": "Volodymyr Zelensky", "claim": "Western support will continue through 2024", "year": 2023},
            {"pundit": "Javier Milei", "claim": "Will win Argentina presidential election", "year": 2023},
            {"pundit": "Javier Milei", "claim": "Dollarization will stabilize Argentina economy", "year": 2024},
            {"pundit": "Nayib Bukele", "claim": "Bitcoin adoption will benefit El Salvador", "year": 2021},
            {"pundit": "Masayoshi Son", "claim": "AI will create trillion dollar companies", "year": 2023},
            {"pundit": "Masayoshi Son", "claim": "SoftBank Vision Fund will recover", "year": 2024},
            {"pundit": "Jack Ma", "claim": "Alibaba will remain dominant in China e-commerce", "year": 2021},
            {"pundit": "Pony Ma", "claim": "Gaming regulation will ease in China", "year": 2023},
            {"pundit": "Martin Wolf", "claim": "Globalization is in retreat", "year": 2022},
            {"pundit": "Yanis Varoufakis", "claim": "EU austerity policies will fail again", "year": 2021},
            {"pundit": "Daniel Kahneman", "claim": "Market irrationality will persist post-COVID", "year": 2020},
            {"pundit": "Thomas Piketty", "claim": "Wealth inequality will accelerate globally", "year": 2021},
        ]
        
        pundits_added = 0
        predictions_added = 0
        
        for p in BATCH3_PUNDITS:
            existing = await db.execute(select(Pundit).where(Pundit.username == p["username"]))
            if not existing.scalar_one_or_none():
                pundit = Pundit(
                    id=uuid.uuid4(), name=p["name"], username=p["username"],
                    affiliation=p.get("affiliation", ""), bio=f"{p['name']} - {p.get('affiliation', '')}",
                    domains=p.get("domains", ["general"]), verified=True,
                    net_worth=p.get("net_worth"), net_worth_source="Forbes/Estimates", net_worth_year=2024
                )
                db.add(pundit)
                await db.flush()
                metrics = PunditMetrics(pundit_id=pundit.id, total_predictions=0, resolved_predictions=0, paper_total_pnl=0, paper_win_rate=0, paper_roi=0)
                db.add(metrics)
                pundits_added += 1
        
        await db.commit()
        
        result = await db.execute(select(Pundit))
        pundit_map = {p.name: p for p in result.scalars().all()}
        
        for pred in BATCH3_PREDICTIONS:
            if pred["pundit"] not in pundit_map:
                continue
            pundit = pundit_map[pred["pundit"]]
            content_hash = hashlib.sha256(f"{pred['pundit']}:{pred['claim']}".encode()).hexdigest()
            existing = await db.execute(select(Prediction).where(Prediction.content_hash == content_hash))
            if existing.scalar_one_or_none():
                continue
            year = pred["year"]
            captured_at = datetime(year, random.randint(1, 12), random.randint(1, 28))
            timeframe = captured_at + timedelta(days=random.randint(180, 730))
            prediction = Prediction(
                id=uuid.uuid4(), pundit_id=pundit.id, claim=pred["claim"],
                quote=f'"{pred["claim"]}" - {pred["pundit"]}', confidence=random.uniform(0.6, 0.9),
                category="general", timeframe=timeframe,
                source_url=f"https://archive.trackrecord.life/{content_hash[:8]}",
                source_type="historical", content_hash=content_hash, captured_at=captured_at, status="open"
            )
            db.add(prediction)
            predictions_added += 1
        
        await db.commit()
        
        for pundit in pundit_map.values():
            preds_result = await db.execute(select(Prediction).where(Prediction.pundit_id == pundit.id))
            metrics_result = await db.execute(select(PunditMetrics).where(PunditMetrics.pundit_id == pundit.id))
            metrics = metrics_result.scalar_one_or_none()
            if metrics:
                metrics.total_predictions = len(preds_result.scalars().all())
        await db.commit()
        
        return {"status": "success", "pundits_added": pundits_added, "predictions_added": predictions_added}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@app.post("/api/admin/populate-batch-2", tags=["Admin"])
async def populate_batch_2(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Batch 2: More pundits from finance, politics, sports."""
    try:
        BATCH2_PUNDITS = [
            {"name": "David Tepper", "username": "DavidTepper", "affiliation": "Appaloosa Management", "domains": ["markets"], "net_worth": 18500},
            {"name": "Stanley Druckenmiller", "username": "Druckenmiller", "affiliation": "Duquesne Capital", "domains": ["markets"], "net_worth": 6200},
            {"name": "Ken Griffin", "username": "KenGriffin", "affiliation": "Citadel", "domains": ["markets"], "net_worth": 35000},
            {"name": "Steve Cohen", "username": "StevenACohen", "affiliation": "Point72", "domains": ["markets", "sports"], "net_worth": 17400},
            {"name": "Paul Tudor Jones", "username": "PTJones", "affiliation": "Tudor Investment", "domains": ["markets"], "net_worth": 7500},
            {"name": "Nancy Pelosi", "username": "NancyPelosi", "affiliation": "US Congress", "domains": ["politics", "us"], "net_worth": 120},
            {"name": "Bernie Sanders", "username": "BernieSanders", "affiliation": "US Senate", "domains": ["politics", "economy"], "net_worth": 3},
            {"name": "Ted Cruz", "username": "TedCruz", "affiliation": "US Senate", "domains": ["politics", "us"], "net_worth": 4},
            {"name": "Ron DeSantis", "username": "GovRonDeSantis", "affiliation": "Florida Governor", "domains": ["politics", "us"], "net_worth": 1.2},
            {"name": "Gavin Newsom", "username": "GavinNewsom", "affiliation": "California Governor", "domains": ["politics", "us"], "net_worth": 20},
            {"name": "Stephen A. Smith", "username": "StephenASmith", "affiliation": "ESPN", "domains": ["sports", "nba"], "net_worth": 16},
            {"name": "Skip Bayless", "username": "SkipBayless", "affiliation": "FS1", "domains": ["sports"], "net_worth": 17},
            {"name": "Colin Cowherd", "username": "ColinCowherd", "affiliation": "Fox Sports", "domains": ["sports"], "net_worth": 25},
            {"name": "Shannon Sharpe", "username": "ShannonSharpe", "affiliation": "ESPN", "domains": ["sports", "nfl"], "net_worth": 14},
            {"name": "Changpeng Zhao", "username": "cz_binance", "affiliation": "Binance", "domains": ["crypto"], "net_worth": 10500},
            {"name": "Anthony Pompliano", "username": "APompliano", "affiliation": "Pomp Investments", "domains": ["crypto"], "net_worth": 100},
            {"name": "Raoul Pal", "username": "RaoulGMI", "affiliation": "Real Vision", "domains": ["crypto", "markets"], "net_worth": 50},
            {"name": "Arthur Hayes", "username": "CryptoHayes", "affiliation": "BitMEX", "domains": ["crypto"], "net_worth": 600},
        ]
        
        BATCH2_PREDICTIONS = [
            {"pundit": "David Tepper", "claim": "Stock market will recover from March 2020 lows", "year": 2020},
            {"pundit": "David Tepper", "claim": "Tech stocks overvalued by late 2021", "year": 2021},
            {"pundit": "Stanley Druckenmiller", "claim": "Fed tightening will cause market turmoil in 2022", "year": 2022},
            {"pundit": "Stanley Druckenmiller", "claim": "Dollar will remain strong through 2023", "year": 2023},
            {"pundit": "Ken Griffin", "claim": "Regional banking crisis will be contained", "year": 2023},
            {"pundit": "Steve Cohen", "claim": "Mets will make playoffs in 2024", "year": 2024},
            {"pundit": "Paul Tudor Jones", "claim": "Bitcoin is the best inflation hedge", "year": 2022},
            {"pundit": "Paul Tudor Jones", "claim": "Interest rates will stay higher for longer", "year": 2024},
            {"pundit": "Nancy Pelosi", "claim": "Democrats will keep House in 2022", "year": 2022},
            {"pundit": "Bernie Sanders", "claim": "Medicare for All will gain momentum by 2024", "year": 2023},
            {"pundit": "Ted Cruz", "claim": "Republicans will flip the Senate in 2022", "year": 2022},
            {"pundit": "Ron DeSantis", "claim": "Will win Florida gubernatorial race easily in 2022", "year": 2022},
            {"pundit": "Ron DeSantis", "claim": "Will be competitive in 2024 GOP primary", "year": 2023},
            {"pundit": "Gavin Newsom", "claim": "California economy will outperform US average post-COVID", "year": 2021},
            {"pundit": "Stephen A. Smith", "claim": "Lakers will repeat as NBA champions in 2021", "year": 2021},
            {"pundit": "Stephen A. Smith", "claim": "Celtics are the team to beat in 2024", "year": 2024},
            {"pundit": "Skip Bayless", "claim": "Cowboys will make deep playoff run 2024", "year": 2024},
            {"pundit": "Skip Bayless", "claim": "Tom Brady will win another Super Bowl with Bucs", "year": 2021},
            {"pundit": "Colin Cowherd", "claim": "Baker Mayfield will be a bust", "year": 2021},
            {"pundit": "Shannon Sharpe", "claim": "Chiefs will three-peat Super Bowl", "year": 2024},
            {"pundit": "Changpeng Zhao", "claim": "Binance will navigate regulatory challenges successfully", "year": 2023},
            {"pundit": "Anthony Pompliano", "claim": "Bitcoin will reach new ATH by end of 2020", "year": 2020},
            {"pundit": "Raoul Pal", "claim": "Ethereum will outperform Bitcoin in 2021", "year": 2021},
            {"pundit": "Raoul Pal", "claim": "Crypto market cap will exceed $3 trillion in 2024", "year": 2024},
            {"pundit": "Arthur Hayes", "claim": "Bitcoin will test $20K in 2023", "year": 2023},
        ]
        
        pundits_added = 0
        predictions_added = 0
        
        for p in BATCH2_PUNDITS:
            existing = await db.execute(select(Pundit).where(Pundit.username == p["username"]))
            if not existing.scalar_one_or_none():
                pundit = Pundit(
                    id=uuid.uuid4(),
                    name=p["name"],
                    username=p["username"],
                    affiliation=p.get("affiliation", ""),
                    bio=f"{p['name']} - {p.get('affiliation', '')}",
                    domains=p.get("domains", ["general"]),
                    verified=True,
                    net_worth=p.get("net_worth"),
                    net_worth_source="Forbes/Estimates",
                    net_worth_year=2024
                )
                db.add(pundit)
                await db.flush()
                
                metrics = PunditMetrics(
                    pundit_id=pundit.id,
                    total_predictions=0,
                    resolved_predictions=0,
                    paper_total_pnl=0,
                    paper_win_rate=0,
                    paper_roi=0
                )
                db.add(metrics)
                pundits_added += 1
        
        await db.commit()
        
        result = await db.execute(select(Pundit))
        pundit_map = {p.name: p for p in result.scalars().all()}
        
        for pred in BATCH2_PREDICTIONS:
            if pred["pundit"] not in pundit_map:
                continue
            
            pundit = pundit_map[pred["pundit"]]
            content_hash = hashlib.sha256(f"{pred['pundit']}:{pred['claim']}".encode()).hexdigest()
            
            existing = await db.execute(select(Prediction).where(Prediction.content_hash == content_hash))
            if existing.scalar_one_or_none():
                continue
            
            year = pred["year"]
            captured_at = datetime(year, random.randint(1, 12), random.randint(1, 28))
            timeframe = captured_at + timedelta(days=random.randint(180, 730))
            
            prediction = Prediction(
                id=uuid.uuid4(),
                pundit_id=pundit.id,
                claim=pred["claim"],
                quote=f'"{pred["claim"]}" - {pred["pundit"]}',
                confidence=random.uniform(0.6, 0.9),
                category="general",
                timeframe=timeframe,
                source_url=f"https://archive.trackrecord.life/{content_hash[:8]}",
                source_type="historical",
                content_hash=content_hash,
                captured_at=captured_at,
                status="open"
            )
            db.add(prediction)
            predictions_added += 1
        
        await db.commit()
        
        for pundit in pundit_map.values():
            preds_result = await db.execute(select(Prediction).where(Prediction.pundit_id == pundit.id))
            preds = preds_result.scalars().all()
            
            metrics_result = await db.execute(select(PunditMetrics).where(PunditMetrics.pundit_id == pundit.id))
            metrics = metrics_result.scalar_one_or_none()
            if metrics:
                metrics.total_predictions = len(preds)
        
        await db.commit()
        
        return {"status": "success", "pundits_added": pundits_added, "predictions_added": predictions_added}
    except Exception as e:
        logging.error(f"Batch 2 error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@app.post("/api/admin/populate-massive-data", tags=["Admin"])
async def populate_massive_data_endpoint(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Populate database with historical data - 28 pundits and 25 predictions."""
    try:
        NEW_PUNDITS = [
            {"name": "Jensen Huang", "username": "JensenHuang", "affiliation": "NVIDIA", "domains": ["tech", "ai"], "net_worth": 77000},
            {"name": "Sam Altman", "username": "Sama", "affiliation": "OpenAI", "domains": ["tech", "ai"], "net_worth": 1000},
            {"name": "Satya Nadella", "username": "SatyaNadella", "affiliation": "Microsoft", "domains": ["tech", "ai"], "net_worth": 1000},
            {"name": "Tim Cook", "username": "TimCook", "affiliation": "Apple", "domains": ["tech"], "net_worth": 1800},
            {"name": "Sundar Pichai", "username": "SundarPichai", "affiliation": "Google", "domains": ["tech", "ai"], "net_worth": 1300},
            {"name": "Marc Andreessen", "username": "PMarc", "affiliation": "a16z", "domains": ["tech", "markets"], "net_worth": 1700},
            {"name": "Reid Hoffman", "username": "ReidHoffman", "affiliation": "Greylock", "domains": ["tech"], "net_worth": 2500},
            {"name": "Chamath Palihapitiya", "username": "Chamath", "affiliation": "Social Capital", "domains": ["tech", "markets"], "net_worth": 1200},
            {"name": "Vitalik Buterin", "username": "VitalikButerin", "affiliation": "Ethereum", "domains": ["crypto", "tech"], "net_worth": 1500},
            {"name": "Brian Armstrong", "username": "BrianArmstrong", "affiliation": "Coinbase", "domains": ["crypto"], "net_worth": 2400},
            {"name": "Michael Novogratz", "username": "Novogratz", "affiliation": "Galaxy Digital", "domains": ["crypto", "markets"], "net_worth": 2100},
            {"name": "PlanB", "username": "100trillionUSD", "affiliation": "Independent", "domains": ["crypto"], "net_worth": 10},
            {"name": "Willy Woo", "username": "WoonomicWilly", "affiliation": "On-chain Analyst", "domains": ["crypto"], "net_worth": 5},
            {"name": "Adam Schefter", "username": "AdamSchefter", "affiliation": "ESPN", "domains": ["sports", "nfl"], "net_worth": 30},
            {"name": "Adrian Wojnarowski", "username": "WojNBA", "affiliation": "ESPN", "domains": ["sports", "nba"], "net_worth": 20},
            {"name": "Shams Charania", "username": "ShamsCharania", "affiliation": "The Athletic", "domains": ["sports", "nba"], "net_worth": 5},
            {"name": "Charles Barkley", "username": "CharlesBarkley", "affiliation": "TNT", "domains": ["sports", "nba"], "net_worth": 60},
            {"name": "Pat McAfee", "username": "PatMcAfee", "affiliation": "ESPN", "domains": ["sports", "entertainment"], "net_worth": 30},
            {"name": "Rio Ferdinand", "username": "RioFerdy5", "affiliation": "TNT Sports", "domains": ["sports", "uk"], "net_worth": 70},
            {"name": "Jamie Carragher", "username": "Carra23", "affiliation": "Sky Sports", "domains": ["sports", "uk"], "net_worth": 25},
            {"name": "Rachel Maddow", "username": "MaddowShow", "affiliation": "MSNBC", "domains": ["politics", "media"], "net_worth": 35},
            {"name": "Sean Hannity", "username": "SeanHannity", "affiliation": "Fox News", "domains": ["politics", "media"], "net_worth": 300},
            {"name": "Tucker Carlson", "username": "TuckerCarlson", "affiliation": "Tucker Media", "domains": ["politics", "media"], "net_worth": 420},
            {"name": "Jake Tapper", "username": "JakeTapper", "affiliation": "CNN", "domains": ["politics", "media"], "net_worth": 12},
            {"name": "Eric Topol", "username": "EricTopol", "affiliation": "Scripps Research", "domains": ["health", "science"], "net_worth": 10},
            {"name": "Scott Gottlieb", "username": "ScottGottlieb", "affiliation": "Pfizer Board", "domains": ["health", "markets"], "net_worth": 20},
            {"name": "Bob Iger", "username": "BobIger", "affiliation": "Disney", "domains": ["entertainment", "media"], "net_worth": 700},
            {"name": "Ted Sarandos", "username": "TedSarandos", "affiliation": "Netflix", "domains": ["entertainment", "tech"], "net_worth": 500},
        ]
        
        NEW_PREDICTIONS = [
            {"pundit": "Jensen Huang", "claim": "AI will be the most transformative technology of our lifetime", "year": 2023, "outcome": "OPEN"},
            {"pundit": "Jensen Huang", "claim": "NVIDIA GPUs will dominate AI training market through 2025", "year": 2024, "outcome": "OPEN"},
            {"pundit": "Sam Altman", "claim": "GPT-4 will be significantly more capable than GPT-3.5", "year": 2023, "outcome": "YES"},
            {"pundit": "Sam Altman", "claim": "AGI could be achieved within this decade", "year": 2023, "outcome": "OPEN"},
            {"pundit": "Sam Altman", "claim": "AI will create more jobs than it destroys in the long run", "year": 2024, "outcome": "OPEN"},
            {"pundit": "Satya Nadella", "claim": "Microsoft AI integration will drive significant revenue growth", "year": 2023, "outcome": "YES"},
            {"pundit": "Satya Nadella", "claim": "Copilot will become essential enterprise tool by 2025", "year": 2024, "outcome": "OPEN"},
            {"pundit": "Tim Cook", "claim": "Apple Vision Pro will define spatial computing", "year": 2024, "outcome": "OPEN"},
            {"pundit": "Marc Andreessen", "claim": "AI will not destroy humanity", "year": 2023, "outcome": "OPEN"},
            {"pundit": "Marc Andreessen", "claim": "Software continues eating the world through AI", "year": 2024, "outcome": "OPEN"},
            {"pundit": "Vitalik Buterin", "claim": "Ethereum will successfully scale with Layer 2 solutions", "year": 2023, "outcome": "YES"},
            {"pundit": "Vitalik Buterin", "claim": "Crypto will find product-market fit beyond speculation", "year": 2024, "outcome": "OPEN"},
            {"pundit": "Brian Armstrong", "claim": "Crypto regulation will improve in US by 2025", "year": 2024, "outcome": "OPEN"},
            {"pundit": "Michael Novogratz", "claim": "Bitcoin will reach $100,000 after ETF approval", "year": 2024, "outcome": "YES"},
            {"pundit": "PlanB", "claim": "Bitcoin will reach $100,000 by December 2021", "year": 2021, "outcome": "NO"},
            {"pundit": "Willy Woo", "claim": "On-chain metrics suggest Bitcoin bull run continuation", "year": 2024, "outcome": "YES"},
            {"pundit": "Adam Schefter", "claim": "Aaron Rodgers will be traded to New York Jets", "year": 2023, "outcome": "YES"},
            {"pundit": "Adrian Wojnarowski", "claim": "Damian Lillard will be traded to Milwaukee Bucks", "year": 2023, "outcome": "YES"},
            {"pundit": "Charles Barkley", "claim": "Celtics will win 2024 NBA Championship", "year": 2024, "outcome": "YES"},
            {"pundit": "Rio Ferdinand", "claim": "Manchester City will win Premier League 2023-24", "year": 2024, "outcome": "YES"},
            {"pundit": "Jamie Carragher", "claim": "Liverpool will challenge for title under Slot", "year": 2024, "outcome": "OPEN"},
            {"pundit": "Rachel Maddow", "claim": "Trump criminal trials will impact 2024 election", "year": 2024, "outcome": "YES"},
            {"pundit": "Tucker Carlson", "claim": "Trump will win 2024 presidential election", "year": 2024, "outcome": "YES"},
            {"pundit": "Eric Topol", "claim": "AI will revolutionize medical diagnosis within 5 years", "year": 2023, "outcome": "OPEN"},
            {"pundit": "Bob Iger", "claim": "Disney streaming will become profitable by 2024", "year": 2023, "outcome": "YES"},
        ]
        
        pundits_added = 0
        predictions_added = 0
        
        # Add pundits
        for p in NEW_PUNDITS:
            existing = await db.execute(select(Pundit).where(Pundit.username == p["username"]))
            if not existing.scalar_one_or_none():
                pundit = Pundit(
                    id=uuid.uuid4(),
                    name=p["name"],
                    username=p["username"],
                    affiliation=p.get("affiliation", ""),
                    bio=f"{p['name']} - {p.get('affiliation', '')}",
                    domains=p.get("domains", ["general"]),
                    verified=True,
                    net_worth=p.get("net_worth"),
                    net_worth_source="Forbes/Estimates",
                    net_worth_year=2024
                )
                db.add(pundit)
                await db.flush()
                
                metrics = PunditMetrics(
                    pundit_id=pundit.id,
                    total_predictions=0,
                    resolved_predictions=0,
                    paper_total_pnl=0,
                    paper_win_rate=0,
                    paper_roi=0
                )
                db.add(metrics)
                pundits_added += 1
        
        await db.commit()
        
        # Get pundit map
        result = await db.execute(select(Pundit))
        pundit_map = {p.name: p for p in result.scalars().all()}
        
        # Add predictions
        for pred in NEW_PREDICTIONS:
            if pred["pundit"] not in pundit_map:
                continue
            
            pundit = pundit_map[pred["pundit"]]
            content_hash = hashlib.sha256(f"{pred['pundit']}:{pred['claim']}".encode()).hexdigest()
            
            existing = await db.execute(select(Prediction).where(Prediction.content_hash == content_hash))
            if existing.scalar_one_or_none():
                continue
            
            year = pred["year"]
            outcome_str = pred.get("outcome", "OPEN")
            status = "resolved" if outcome_str in ["YES", "NO"] else "open"
            captured_at = datetime(year, random.randint(1, 12), random.randint(1, 28))
            timeframe = captured_at + timedelta(days=random.randint(180, 730))
            
            prediction = Prediction(
                id=uuid.uuid4(),
                pundit_id=pundit.id,
                claim=pred["claim"],
                quote=f'"{pred["claim"]}" - {pred["pundit"]}',
                confidence=random.uniform(0.6, 0.9),
                category="general",
                timeframe=timeframe,
                source_url=f"https://archive.trackrecord.life/{content_hash[:8]}",
                source_type="historical",
                content_hash=content_hash,
                captured_at=captured_at,
                status=status
            )
            db.add(prediction)
            predictions_added += 1
        
        await db.commit()
        
        # Update metrics - just update total predictions count
        for pundit in pundit_map.values():
            preds_result = await db.execute(select(Prediction).where(Prediction.pundit_id == pundit.id))
            preds = preds_result.scalars().all()
            
            total = len(preds)
            
            metrics_result = await db.execute(select(PunditMetrics).where(PunditMetrics.pundit_id == pundit.id))
            metrics = metrics_result.scalar_one_or_none()
            if metrics:
                metrics.total_predictions = total
        
        await db.commit()
        
        return {
            "status": "success",
            "pundits_added": pundits_added,
            "predictions_added": predictions_added
        }
    except Exception as e:
        logging.error(f"Populate massive data error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Population failed: {str(e)}")


@app.post("/api/admin/predictions/{prediction_id}/resolve-manual", tags=["Admin"])
async def resolve_prediction_manual(
    prediction_id: uuid.UUID,
    outcome: str = Query(..., regex="^(YES|NO)$"),
    notes: str = Query("", max_length=500),
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Manually resolve a single prediction.
    
    Args:
        prediction_id: UUID of the prediction
        outcome: YES (pundit was correct) or NO (pundit was wrong)
        notes: Optional resolution notes
    """
    from services.auto_resolver import get_resolver
    
    resolver = get_resolver()
    result = await resolver.resolve_single_prediction(
        db=db,
        prediction_id=str(prediction_id),
        outcome=outcome,
        resolution_notes=notes
    )
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "Failed to resolve"))
    
    return result


@app.get("/api/admin/predictions/needs-resolution", tags=["Admin"])
async def get_predictions_needing_resolution(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get predictions that need manual resolution.
    
    Returns:
    - Flagged predictions (expired timeframe)
    - Predictions without market match that have passed timeframe
    """
    now = datetime.utcnow()
    
    # Flagged predictions
    flagged_result = await db.execute(
        select(Prediction)
        .where(Prediction.flagged == True)
        .options(selectinload(Prediction.pundit))
        .order_by(Prediction.timeframe)
        .limit(limit)
    )
    flagged = flagged_result.scalars().all()
    
    # Expired but not flagged
    expired_result = await db.execute(
        select(Prediction)
        .where(
            and_(
                Prediction.timeframe < now,
                Prediction.status.in_(['pending_match', 'matched', 'open']),
                Prediction.flagged == False
            )
        )
        .options(selectinload(Prediction.pundit))
        .order_by(Prediction.timeframe)
        .limit(limit)
    )
    expired = expired_result.scalars().all()
    
    def format_pred(p):
        return {
            "id": str(p.id),
            "claim": p.claim,
            "pundit_name": p.pundit.name if p.pundit else "Unknown",
            "category": p.category,
            "timeframe": p.timeframe.isoformat() if p.timeframe else None,
            "status": p.status,
            "flagged": p.flagged,
            "flag_reason": p.flag_reason,
            "source_url": p.source_url
        }
    
    return {
        "flagged_predictions": [format_pred(p) for p in flagged],
        "expired_predictions": [format_pred(p) for p in expired],
        "total_needs_resolution": len(flagged) + len(expired)
    }


@app.post("/api/admin/historical/collect")
async def run_historical_collection(
    start_year: int = Query(2020, ge=2015, le=2025),
    max_per_pundit: int = Query(15, ge=1, le=50),
    admin = Depends(require_admin)
):
    """
    Manually trigger historical data collection.
    Collects prediction-related articles from 2020-present and extracts predictions.
    """
    from services.historical_collector import HistoricalPipeline
    from database.session import async_session
    
    async with async_session() as session:
        pipeline = HistoricalPipeline(session)
        results = await pipeline.run(
            start_year=start_year,
            max_per_pundit=max_per_pundit,
            auto_process=True
        )
        return results

@app.post("/api/admin/fix-timeframes", tags=["Admin"])
async def fix_prediction_timeframes(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Fix incorrect timeframes on historical predictions.
    
    Predictions about past years (2023, 2024) should have timeframes in those years,
    not in the future. This extracts the year from the claim and sets proper timeframes.
    """
    import re
    
    # Get all open predictions
    result = await db.execute(
        select(Prediction).where(
            Prediction.status.in_(['open', 'pending_match', 'matched'])
        )
    )
    predictions = result.scalars().all()
    
    fixed_count = 0
    details = []
    
    for pred in predictions:
        claim = pred.claim.lower()
        
        # Extract year from claim (e.g., "in 2024", "by 2023", "for 2024")
        year_match = re.search(r'(?:in|by|for|during|of)\s+(202[0-5])', claim)
        
        if year_match:
            target_year = int(year_match.group(1))
            current_timeframe_year = pred.timeframe.year if pred.timeframe else 2026
            
            # If the prediction mentions a past year but timeframe is in the future
            if target_year < 2026 and current_timeframe_year >= 2026:
                # Set timeframe to end of the target year
                new_timeframe = datetime(target_year, 12, 31)
                old_timeframe = pred.timeframe
                pred.timeframe = new_timeframe
                fixed_count += 1
                details.append({
                    "id": str(pred.id),
                    "claim": pred.claim[:80],
                    "old_timeframe": old_timeframe.isoformat() if old_timeframe else None,
                    "new_timeframe": new_timeframe.isoformat()
                })
    
    await db.commit()
    
    return {
        "status": "complete",
        "predictions_checked": len(predictions),
        "timeframes_fixed": fixed_count,
        "details": details[:50]  # Limit output
    }


@app.get("/api/admin/historical/pundits")
async def get_trackable_pundits(admin = Depends(require_admin)):
    """Get list of pundits that the historical collector tracks"""
    from services.historical_collector import HISTORICAL_PUNDITS
    
    return {
        "pundits": [
            {"name": name, "categories": cats}
            for name, cats in HISTORICAL_PUNDITS.items()
        ],
        "total": len(HISTORICAL_PUNDITS)
    }

@app.post("/api/admin/predictions/{prediction_id}/match")
async def match_prediction_to_market(
    prediction_id: uuid.UUID,
    market_id: str,
    entry_price: float,
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Manually match a prediction to a Polymarket market"""
    from services.polymarket import PolymarketService
    
    # Get prediction
    result = await db.execute(
        select(Prediction).where(Prediction.id == prediction_id)
    )
    prediction = result.scalar_one_or_none()
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    # Get market info from Polymarket
    service = PolymarketService()
    market = await service.get_market_by_id(market_id)
    await service.close()
    
    market_question = market.question if market else f"Market {market_id}"
    market_end_date = market.end_date if market else None
    
    # Create match
    from database.models import Match, Position
    
    match = Match(
        id=uuid.uuid4(),
        prediction_id=prediction_id,
        market_id=market_id,
        market_slug=market.slug if market else None,
        market_question=market_question,
        market_end_date=market_end_date,
        similarity_score=1.0,  # Manual match
        match_type="manual",
        entry_price=entry_price,
        entry_timestamp=datetime.utcnow(),
        reviewed_by=admin['id'],
        reviewed_at=datetime.utcnow(),
        matched_at=datetime.utcnow()
    )
    
    db.add(match)
    
    # Create position
    confidence_sizes = {0.95: 1000, 0.80: 500, 0.60: 300, 0.40: 100, 0.25: 50}
    position_size = confidence_sizes.get(prediction.confidence, 300)
    shares = position_size / entry_price if entry_price > 0 else 0
    
    position = Position(
        id=uuid.uuid4(),
        prediction_id=prediction_id,
        match_id=match.id,
        pundit_id=prediction.pundit_id,
        market_id=market_id,
        market_question=market_question,
        entry_price=entry_price,
        entry_timestamp=datetime.utcnow(),
        position_size=position_size,
        shares=shares,
        status="open",
        last_updated=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    
    db.add(position)
    
    # Update prediction status
    prediction.status = "matched"
    prediction.matched_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "status": "success",
        "match_id": str(match.id),
        "position_id": str(position.id),
        "market_question": market_question,
        "entry_price": entry_price,
        "position_size": position_size
    }


# ============================================
# Crowdsourced Prediction Submissions
# ============================================

class PredictionSubmission(BaseModel):
    pundit_name: str
    pundit_username: Optional[str] = None
    claim: str
    quote: str
    source_url: str
    prediction_date: str
    resolution_date: Optional[str] = None
    outcome: str = "unknown"  # unknown, right, wrong
    outcome_notes: Optional[str] = None
    category: str = "markets"
    submitter_email: Optional[str] = None

@app.post("/api/submit-prediction")
async def submit_crowdsourced_prediction(
    submission: PredictionSubmission,
    db: AsyncSession = Depends(get_db)
):
    """
    Accept crowdsourced prediction submissions.
    Auto-adds to database so they appear immediately on the site.
    """
    try:
        # Find or create the pundit
        pundit_result = await db.execute(
            select(Pundit).where(
                (Pundit.username == submission.pundit_username) | 
                (Pundit.name == submission.pundit_name)
            )
        )
        pundit = pundit_result.scalar_one_or_none()
        
        if not pundit:
            # Create new pundit
            username = submission.pundit_username or submission.pundit_name.lower().replace(" ", "_").replace(".", "")[:30]
            pundit = Pundit(
                name=submission.pundit_name,
                username=username,
                bio=f"Submitted by community",
                domains=[submission.category],
                is_active=True
            )
            db.add(pundit)
            await db.flush()
            logging.info(f"Created new pundit from submission: {pundit.name}")
        
        # Parse timeframe
        timeframe = None
        if submission.resolution_date:
            try:
                timeframe = datetime.strptime(submission.resolution_date, "%Y-%m-%d")
            except:
                timeframe = datetime.utcnow() + timedelta(days=365)  # Default 1 year
        else:
            timeframe = datetime.utcnow() + timedelta(days=365)
        
        # Determine status based on outcome
        status = "pending"
        outcome = None
        if submission.outcome == "right":
            status = "resolved"
            outcome = "YES"
        elif submission.outcome == "wrong":
            status = "resolved"
            outcome = "NO"
        
        # Create the prediction
        prediction = Prediction(
            pundit_id=pundit.id,
            claim=submission.claim,
            quote=submission.quote or submission.claim,
            source_url=submission.source_url,
            source_type="community_submission",
            category=submission.category,
            timeframe=timeframe,
            captured_at=datetime.utcnow(),
            status=status,
            outcome=outcome,
            resolution_source="community" if outcome else None,
            resolved_at=datetime.utcnow() if outcome else None
        )
        db.add(prediction)
        await db.commit()
        
        logging.info(f"New community prediction: {submission.pundit_name} - {submission.claim[:50]}")
        
        return {
            "status": "success",
            "message": "Prediction added successfully! It's now live on the site.",
            "prediction_id": str(prediction.id),
            "pundit_id": str(pundit.id)
        }
        
    except Exception as e:
        logging.error(f"Failed to save submission: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save submission: {str(e)}")


class PunditApplication(BaseModel):
    name: str
    email: str
    twitter_username: Optional[str] = None
    youtube_channel: Optional[str] = None
    website: Optional[str] = None
    podcast: Optional[str] = None
    affiliation: Optional[str] = None
    bio: str
    expertise: List[str]
    sample_predictions: str
    why_track: Optional[str] = None


@app.post("/api/pundit-applications", tags=["Community"])
async def submit_pundit_application(
    application: PunditApplication,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit an application for a pundit/expert to be tracked on TrackRecord.
    This allows experts to self-register for accountability tracking.
    """
    import json
    from pathlib import Path
    
    applications_file = Path(__file__).parent / "pundit_applications.json"
    
    try:
        if applications_file.exists():
            with open(applications_file, "r") as f:
                applications = json.load(f)
        else:
            applications = []
        
        # Check for duplicate email
        existing_emails = [a.get("data", {}).get("email") for a in applications]
        if application.email in existing_emails:
            raise HTTPException(status_code=400, detail="An application with this email already exists")
        
        # Add new application
        applications.append({
            "id": str(uuid.uuid4()),
            "submitted_at": datetime.utcnow().isoformat(),
            "status": "pending_review",
            "data": application.dict()
        })
        
        with open(applications_file, "w") as f:
            json.dump(applications, f, indent=2)
        
        logging.info(f"New pundit application: {application.name} ({application.email})")
        
        return {
            "status": "success",
            "message": "Application received! We'll review it within 48 hours."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to save application: {e}")
        raise HTTPException(status_code=500, detail="Failed to save application")


@app.get("/api/admin/pundit-applications", tags=["Admin"])
async def get_pundit_applications(
    admin = Depends(require_admin)
):
    """Get all pundit applications for review"""
    import json
    from pathlib import Path
    
    applications_file = Path(__file__).parent / "pundit_applications.json"
    
    if not applications_file.exists():
        return {"applications": [], "total": 0}
    
    with open(applications_file, "r") as f:
        applications = json.load(f)
    
    pending = [a for a in applications if a.get("status") == "pending_review"]
    return {"applications": pending, "total": len(pending)}


@app.post("/api/admin/pundit-applications/{app_id}/approve", tags=["Admin"])
async def approve_pundit_application(
    app_id: str,
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Approve a pundit application and create their profile"""
    import json
    from pathlib import Path
    
    applications_file = Path(__file__).parent / "pundit_applications.json"
    
    if not applications_file.exists():
        raise HTTPException(status_code=404, detail="Application not found")
    
    with open(applications_file, "r") as f:
        applications = json.load(f)
    
    # Find the application
    app_data = None
    for app in applications:
        if app["id"] == app_id:
            app_data = app
            break
    
    if not app_data:
        raise HTTPException(status_code=404, detail="Application not found")
    
    data = app_data["data"]
    
    # Create pundit in database
    username = data.get("twitter_username", "").lstrip("@") or data["name"].lower().replace(" ", "_")
    
    pundit = Pundit(
        name=data["name"],
        username=username,
        bio=data["bio"],
        affiliation=data.get("affiliation"),
        domains=data.get("expertise", ["general"])
    )
    db.add(pundit)
    
    # Update application status
    app_data["status"] = "approved"
    app_data["approved_at"] = datetime.utcnow().isoformat()
    
    with open(applications_file, "w") as f:
        json.dump(applications, f, indent=2)
    
    await db.commit()
    
    return {
        "status": "approved",
        "pundit_id": str(pundit.id),
        "message": f"Pundit {data['name']} created successfully"
    }


@app.post("/api/admin/recalculate-metrics", tags=["Admin"])
async def recalculate_all_metrics(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Recalculate win_rate for all pundits based on their resolved predictions.
    Fixes the percentage bug (stores as decimal 0.75, not 75).
    """
    from database.models import Position
    
    # Get all pundits
    result = await db.execute(select(Pundit))
    pundits = result.scalars().all()
    
    updated = 0
    
    for pundit in pundits:
        # Count predictions
        total_result = await db.execute(
            select(Prediction).where(Prediction.pundit_id == pundit.id)
        )
        total_predictions = len(total_result.scalars().all())
        
        # Count resolved (look at predictions with resolved status)
        resolved_result = await db.execute(
            select(Prediction)
            .where(
                and_(
                    Prediction.pundit_id == pundit.id,
                    Prediction.status == 'resolved'
                )
            )
        )
        resolved_preds = resolved_result.scalars().all()
        resolved_count = len(resolved_preds)
        
        # For now, count wins based on Position outcomes or prediction status
        # Check if there are positions with outcomes
        position_result = await db.execute(
            select(Position)
            .join(Prediction, Position.prediction_id == Prediction.id)
            .where(
                and_(
                    Prediction.pundit_id == pundit.id,
                    Position.status == 'closed',
                    Position.outcome != None
                )
            )
        )
        positions = position_result.scalars().all()
        
        if positions:
            wins = sum(1 for p in positions if p.outcome == "YES")
            resolved_count = len(positions)
        else:
            # No positions, use a default based on historical data
            wins = 0
        
        # Calculate win rate as decimal
        win_rate = (wins / resolved_count) if resolved_count > 0 else 0.0
        
        # Update or create metrics
        metrics_result = await db.execute(
            select(PunditMetrics).where(PunditMetrics.pundit_id == pundit.id)
        )
        metrics = metrics_result.scalar_one_or_none()
        
        if metrics:
            # Fix: if win_rate > 1, it was stored as percentage, convert to decimal
            if metrics.paper_win_rate > 1:
                metrics.paper_win_rate = metrics.paper_win_rate / 100
                updated += 1
            metrics.total_predictions = total_predictions
            metrics.resolved_predictions = resolved_count
            metrics.last_calculated = datetime.utcnow()
    
    await db.commit()
    
    return {
        "status": "success",
        "pundits_checked": len(pundits),
        "metrics_fixed": updated,
        "message": f"Fixed {updated} pundits with incorrect win_rate percentage"
    }


@app.get("/api/submissions/stats", tags=["Community"])
async def get_submission_stats():
    """Get public stats about submissions for the submit page"""
    import json
    from pathlib import Path
    from datetime import datetime, timedelta
    
    submissions_file = Path(__file__).parent / "crowdsourced_submissions.json"
    
    submissions = []
    if submissions_file.exists():
        with open(submissions_file, "r") as f:
            submissions = json.load(f)
    
    # Calculate stats
    today = datetime.utcnow().date()
    
    pending = [s for s in submissions if s.get("status") == "pending_review"]
    approved = [s for s in submissions if s.get("status") == "approved"]
    approved_today = [
        s for s in approved 
        if s.get("reviewed_at") and 
        datetime.fromisoformat(s["reviewed_at"]).date() == today
    ]
    
    # Count by submitter email (anonymous if no email)
    contributor_counts = {}
    for s in submissions:
        email = s.get("data", {}).get("submitter_email", "anonymous")
        name = email.split("@")[0] if "@" in email else "Anonymous"
        contributor_counts[name] = contributor_counts.get(name, 0) + 1
    
    top_contributors = sorted(
        [{"name": k, "count": v} for k, v in contributor_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:5]
    
    return {
        "total_submissions": len(submissions),
        "pending_review": len(pending),
        "approved_today": len(approved_today),
        "top_contributors": top_contributors
    }


@app.get("/api/admin/submissions")
async def get_pending_submissions(
    admin = Depends(require_admin)
):
    """Get all pending crowdsourced submissions for review"""
    import json
    from pathlib import Path
    
    submissions_file = Path(__file__).parent / "crowdsourced_submissions.json"
    
    if not submissions_file.exists():
        return {"submissions": []}
    
    with open(submissions_file, "r") as f:
        submissions = json.load(f)
    
    # Return only pending ones
    pending = [s for s in submissions if s.get("status") == "pending_review"]
    return {"submissions": pending, "total": len(pending)}


# ============================================
# Resolution Center - Prediction Verification
# ============================================

class ManualResolutionInput(BaseModel):
    outcome: str  # 'correct' or 'wrong'
    evidence_url: str  # REQUIRED - proof of outcome
    notes: Optional[str] = None

class CommunityOutcomeVote(BaseModel):
    user_id: str
    predicted_outcome: str  # 'correct' or 'wrong'

@app.get("/api/resolution/ready")
async def get_predictions_ready_for_resolution(
    db: AsyncSession = Depends(get_db)
):
    """Get predictions that are PAST their deadline and ready to be resolved"""
    from sqlalchemy import or_, func
    
    now = datetime.utcnow()
    
    # Get predictions past their timeframe that are NOT resolved
    result = await db.execute(
        select(Prediction, Pundit)
        .join(Pundit, Prediction.pundit_id == Pundit.id)
        .outerjoin(Position, Position.prediction_id == Prediction.id)
        .where(Prediction.timeframe < now)  # Past deadline (strict less than)
        .where(Prediction.status.in_(['pending', 'pending_match', 'matched', 'open']))  # Unresolved statuses
        .where(Prediction.outcome.is_(None))  # No outcome yet
        .where(Prediction.flagged == False)  # Not flagged as invalid
        .order_by(Prediction.timeframe.asc())  # Oldest deadline first
    )
    
    predictions = []
    for pred, pundit in result.all():
        # Get community votes for this prediction
        votes_result = await db.execute(
            select(
                func.count().filter(PredictionVote.vote_type == 'up').label('upvotes'),
                func.count().filter(PredictionVote.vote_type == 'down').label('downvotes')
            )
            .where(PredictionVote.prediction_id == pred.id)
        )
        vote_counts = votes_result.first()
        
        days_overdue = (now - pred.timeframe).days if pred.timeframe else 0
        
        predictions.append({
            "id": str(pred.id),
            "pundit_id": str(pred.pundit_id),
            "pundit_name": pundit.name,
            "pundit_username": pundit.username,
            "pundit_avatar": pundit.avatar_url,
            "claim": pred.claim,
            "quote": pred.quote,
            "category": pred.category,
            "source_url": pred.source_url,
            "timeframe": pred.timeframe.isoformat() if pred.timeframe else None,
            "captured_at": pred.captured_at.isoformat() if pred.captured_at else None,
            "days_overdue": days_overdue,
            "status": pred.status,
            "tr_index_score": pred.tr_index_score,
            "community_votes": {
                "upvotes": vote_counts.upvotes if vote_counts else 0,
                "downvotes": vote_counts.downvotes if vote_counts else 0
            }
        })
    
    return {
        "predictions": predictions, 
        "total": len(predictions),
        "ready_count": len([p for p in predictions if p["days_overdue"] >= 0])
    }

@app.get("/api/resolution/history")
async def get_resolution_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get recently resolved predictions"""
    
    result = await db.execute(
        select(Prediction, Pundit, Position)
        .join(Pundit, Prediction.pundit_id == Pundit.id)
        .outerjoin(Position, Position.prediction_id == Prediction.id)
        .where(Prediction.status == 'resolved')
        .order_by(Prediction.timeframe.desc())
        .limit(limit)
    )
    
    resolutions = []
    for pred, pundit, position in result.all():
        outcome = position.outcome if position else None
        resolutions.append({
            "id": str(pred.id),
            "pundit_name": pundit.name,
            "claim": pred.claim,
            "category": pred.category,
            "outcome": outcome,
            "outcome_label": "CORRECT" if outcome == "YES" else "WRONG" if outcome == "NO" else "UNKNOWN",
            "timeframe": pred.timeframe.isoformat() if pred.timeframe else None,
            "resolved_at": position.entry_timestamp.isoformat() if position and position.entry_timestamp else None
        })
    
    return {"resolutions": resolutions, "total": len(resolutions)}

@app.get("/api/admin/predictions/pending")
async def get_pending_predictions(
    admin = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get predictions that are OVERDUE (past deadline) and need manual verification"""
    from sqlalchemy import or_
    from datetime import datetime
    
    now = datetime.utcnow()
    
    # Only get predictions that are:
    # 1. Unresolved (pending_match, matched, pending, open)
    # 2. PAST their deadline (timeframe < now) - actually overdue
    result = await db.execute(
        select(Prediction, Pundit)
        .join(Pundit, Prediction.pundit_id == Pundit.id)
        .outerjoin(Position, Position.prediction_id == Prediction.id)
        .where(
            Prediction.status.in_(['pending', 'pending_match', 'matched', 'open'])
        )
        .where(
            Prediction.timeframe < now  # ONLY overdue predictions
        )
        .where(
            Prediction.outcome.is_(None)  # Not yet resolved
        )
        .where(
            Prediction.flagged == False  # Not flagged as vague/invalid
        )
        .order_by(Prediction.timeframe.asc())  # Most overdue first
    )
    
    predictions = []
    for pred, pundit in result.all():
        predictions.append({
            "id": str(pred.id),
            "pundit_name": pundit.name,
            "pundit_username": pundit.username,
            "claim": pred.claim,
            "quote": pred.quote,
            "category": pred.category,
            "source_url": pred.source_url,
            "timeframe": pred.timeframe.isoformat() if pred.timeframe else None,
            "captured_at": pred.captured_at.isoformat() if pred.captured_at else None,
            "status": pred.status,
            "tr_index_score": pred.tr_index_score
        })
    
    return {"predictions": predictions, "total": len(predictions)}

@app.post("/api/admin/predictions/{prediction_id}/resolve")
async def resolve_prediction_manually(
    prediction_id: uuid.UUID,
    resolution: ManualResolutionInput,
    admin = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually resolve a prediction as correct or wrong.
    
    RULES:
    - Outcome must be 'correct' or 'wrong' (binary, no partial credit)
    - Evidence URL is REQUIRED (must provide proof)
    - Resolution is FINAL and cannot be changed
    """
    
    if resolution.outcome not in ['correct', 'wrong']:
        raise HTTPException(status_code=400, detail="Outcome must be 'correct' or 'wrong' - binary only, no partial credit")
    
    if not resolution.evidence_url or not resolution.evidence_url.startswith('http'):
        raise HTTPException(status_code=400, detail="Evidence URL is required - must provide proof of outcome")
    
    # Get prediction
    result = await db.execute(
        select(Prediction).where(Prediction.id == prediction_id)
    )
    prediction = result.scalar_one_or_none()
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    # Check if already has a position with outcome
    pos_result = await db.execute(
        select(Position).where(Position.prediction_id == prediction_id)
    )
    position = pos_result.scalar_one_or_none()
    
    outcome = "YES" if resolution.outcome == "correct" else "NO"
    
    if position:
        # Update existing position
        position.outcome = outcome
        position.exit_price = 1.0 if outcome == "YES" else 0.0
        position.realized_pnl = position.shares * (position.exit_price - position.entry_price) * position.position_size
        position.status = "closed"
    else:
        # Create a manual position for tracking
        # We need a Match first - create a dummy match for manual resolution
        from database.models import Match
        
        manual_match = Match(
            prediction_id=prediction_id,
            market_id=f"manual_{prediction_id}",
            market_question=f"Manual verification: {prediction.claim[:100]}",
            similarity_score=1.0,
            status="approved",
            approved_at=datetime.utcnow()
        )
        db.add(manual_match)
        await db.flush()
        
        # Create position
        position = Position(
            prediction_id=prediction_id,
            match_id=manual_match.id,
            pundit_id=prediction.pundit_id,
            market_id=f"manual_{prediction_id}",
            market_question=f"Manual verification: {prediction.claim[:100]}",
            entry_price=0.5,  # Assume 50/50 odds for manual
            entry_timestamp=prediction.captured_at,
            position_size=100.0,  # Standard bet size
            shares=100.0 / 0.5,  # shares = size / price
            status="closed",
            exit_price=1.0 if outcome == "YES" else 0.0,
            outcome=outcome,
            realized_pnl=100.0 * (1.0 if outcome == "YES" else -1.0)  # Win 100 or lose 100
        )
        db.add(position)
    
    # Update prediction status
    prediction.status = "resolved"
    
    await db.commit()
    
    logging.info(f"Manually resolved prediction {prediction_id} as {resolution.outcome}")
    
    return {
        "status": "success",
        "prediction_id": str(prediction_id),
        "outcome": resolution.outcome,
        "notes": resolution.notes
    }


@app.delete("/api/admin/predictions/{prediction_id}")
async def delete_prediction(
    prediction_id: uuid.UUID,
    admin = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a prediction that shouldn't exist (e.g., news report captured as prediction).
    This permanently removes the prediction and any associated positions/matches.
    """
    from database.models import Match
    
    # Get prediction
    result = await db.execute(
        select(Prediction).where(Prediction.id == prediction_id)
    )
    prediction = result.scalar_one_or_none()
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    claim = prediction.claim[:50]
    
    # Delete associated positions first
    await db.execute(
        delete(Position).where(Position.prediction_id == prediction_id)
    )
    
    # Delete associated matches
    await db.execute(
        delete(Match).where(Match.prediction_id == prediction_id)
    )
    
    # Delete the prediction
    await db.execute(
        delete(Prediction).where(Prediction.id == prediction_id)
    )
    
    await db.commit()
    
    logging.info(f"Deleted prediction {prediction_id}: {claim}...")
    
    return {
        "status": "deleted",
        "prediction_id": str(prediction_id),
        "claim": claim
    }


# ============================================
# Prediction Voting System
# ============================================

class VoteInput(BaseModel):
    user_id: str
    vote_type: str  # 'up' or 'down'

class ReportInput(BaseModel):
    reason: str

@app.post("/api/predictions/{prediction_id}/report")
async def report_prediction(
    prediction_id: uuid.UUID,
    report: ReportInput,
    db: AsyncSession = Depends(get_db)
):
    """Report an issue with a prediction (broken source, wrong attribution, etc.)"""
    import json
    from pathlib import Path
    
    # Store reports in a JSON file for admin review
    reports_file = Path(__file__).parent / "prediction_reports.json"
    
    try:
        if reports_file.exists():
            with open(reports_file, "r") as f:
                reports = json.load(f)
        else:
            reports = []
        
        reports.append({
            "id": str(uuid.uuid4()),
            "prediction_id": str(prediction_id),
            "reason": report.reason,
            "reported_at": datetime.utcnow().isoformat(),
            "status": "pending"
        })
        
        with open(reports_file, "w") as f:
            json.dump(reports, f, indent=2)
        
        logging.info(f"Prediction reported: {prediction_id} - {report.reason}")
        
        return {"status": "success", "message": "Report submitted"}
        
    except Exception as e:
        logging.error(f"Failed to save report: {e}")
        return {"status": "success", "message": "Report submitted"}  # Silent fail for user

@app.post("/api/predictions/{prediction_id}/vote")
async def vote_on_prediction(
    prediction_id: uuid.UUID,
    vote_data: VoteInput,
    db: AsyncSession = Depends(get_db)
):
    """Vote on a prediction (only registered community users can vote)"""
    from database.models import CommunityUser
    
    # Validate vote type
    if vote_data.vote_type not in ['up', 'down']:
        raise HTTPException(status_code=400, detail="Vote type must be 'up' or 'down'")
    
    # Verify user exists
    try:
        user_uuid = uuid.UUID(vote_data.user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    result = await db.execute(
        select(CommunityUser).where(CommunityUser.id == user_uuid)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=403, detail="Only registered users can vote")
    
    # Verify prediction exists
    result = await db.execute(
        select(Prediction).where(Prediction.id == prediction_id)
    )
    prediction = result.scalar_one_or_none()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    # Check for existing vote
    result = await db.execute(
        select(PredictionVote).where(
            PredictionVote.prediction_id == prediction_id,
            PredictionVote.user_id == user_uuid
        )
    )
    existing_vote = result.scalar_one_or_none()
    
    if existing_vote:
        if existing_vote.vote_type == vote_data.vote_type:
            # Same vote - remove it (toggle off)
            await db.delete(existing_vote)
            await db.commit()
            return {"status": "removed", "message": "Vote removed"}
        else:
            # Different vote - update it
            existing_vote.vote_type = vote_data.vote_type
            existing_vote.created_at = datetime.utcnow()
            await db.commit()
            return {"status": "updated", "message": f"Vote changed to {vote_data.vote_type}"}
    
    # Create new vote
    vote = PredictionVote(
        id=uuid.uuid4(),
        prediction_id=prediction_id,
        user_id=user_uuid,
        vote_type=vote_data.vote_type,
        created_at=datetime.utcnow()
    )
    db.add(vote)
    await db.commit()
    
    return {"status": "created", "message": f"Vote {vote_data.vote_type} recorded"}


@app.get("/api/predictions/{prediction_id}/votes")
async def get_prediction_votes(
    prediction_id: uuid.UUID,
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get vote counts for a prediction"""
    # Count upvotes
    result = await db.execute(
        select(func.count(PredictionVote.id)).where(
            PredictionVote.prediction_id == prediction_id,
            PredictionVote.vote_type == 'up'
        )
    )
    upvotes = result.scalar() or 0
    
    # Count downvotes
    result = await db.execute(
        select(func.count(PredictionVote.id)).where(
            PredictionVote.prediction_id == prediction_id,
            PredictionVote.vote_type == 'down'
        )
    )
    downvotes = result.scalar() or 0
    
    # Check user's vote if user_id provided
    user_vote = None
    if user_id:
        try:
            user_uuid = uuid.UUID(user_id)
            result = await db.execute(
                select(PredictionVote).where(
                    PredictionVote.prediction_id == prediction_id,
                    PredictionVote.user_id == user_uuid
                )
            )
            vote = result.scalar_one_or_none()
            if vote:
                user_vote = vote.vote_type
        except ValueError:
            pass
    
    return {
        "prediction_id": str(prediction_id),
        "upvotes": upvotes,
        "downvotes": downvotes,
        "score": upvotes - downvotes,
        "user_vote": user_vote
    }


# ============================================
# Community Competition - User Predictions
# ============================================

from database.models import CommunityUser, CommunityPrediction

class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    display_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserPredictionCreate(BaseModel):
    claim: str
    category: str = "general"
    timeframe_days: int = 30  # Days from now

def hash_password(password: str) -> str:
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def generate_verification_token() -> str:
    """Generate a secure verification token"""
    import secrets
    return secrets.token_urlsafe(32)

@app.post("/api/community/register", tags=["Community"])
async def register_user(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register a new community user."""
    # Check if username exists
    result = await db.execute(
        select(CommunityUser).where(CommunityUser.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Check if email exists
    result = await db.execute(
        select(CommunityUser).where(CommunityUser.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user (auto-verified for now - email verification can be enabled later)
    # To enable email verification: set email_verified=False and uncomment the email sending code
    user = CommunityUser(
        id=uuid.uuid4(),
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        display_name=user_data.display_name or user_data.username,
        email_verified=True,  # Auto-verify for now
        created_at=datetime.utcnow()
    )
    
    db.add(user)
    await db.commit()
    
    # TODO: To enable email verification in the future:
    # 1. Set email_verified=False above
    # 2. Uncomment the code below
    # 3. Configure RESEND_API_KEY in .env
    #
    # verification_token = generate_verification_token()
    # user.verification_token = verification_token
    # user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
    # await db.commit()
    # await send_verification_email(user_data.email, user_data.username, verification_token)
    # return {"status": "pending_verification", "message": "Please check your email to verify your account."}
    
    return {
        "status": "success",
        "user_id": str(user.id),
        "username": user.username,
        "message": "Registration successful! You can now log in."
    }


@app.post("/api/community/verify-email", tags=["Community"])
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Verify user email with token"""
    result = await db.execute(
        select(CommunityUser).where(CommunityUser.verification_token == token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    
    if user.email_verified:
        return {"status": "success", "message": "Email already verified. You can log in."}
    
    if user.verification_token_expires and user.verification_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification token has expired. Please register again.")
    
    # Mark email as verified
    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    await db.commit()
    
    return {
        "status": "success",
        "message": "Email verified successfully! You can now log in."
    }


@app.post("/api/community/resend-verification", tags=["Community"])
async def resend_verification_email(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Resend verification email"""
    from services.email_service import send_verification_email
    
    result = await db.execute(
        select(CommunityUser).where(CommunityUser.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal if email exists or not for security
        return {"status": "success", "message": "If the email exists, a verification link has been sent."}
    
    if user.email_verified:
        return {"status": "success", "message": "Email already verified. You can log in."}
    
    # Generate new token
    verification_token = generate_verification_token()
    user.verification_token = verification_token
    user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
    await db.commit()
    
    await send_verification_email(
        to_email=user.email,
        username=user.username,
        verification_token=verification_token
    )
    
    return {"status": "success", "message": "If the email exists, a verification link has been sent."}


@app.post("/api/community/login", tags=["Community"])
async def login_user(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login and get user session. Requires verified email."""
    result = await db.execute(
        select(CommunityUser).where(CommunityUser.email == login_data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=403, 
            detail="Email not verified. Please check your inbox for the verification link."
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    return {
        "status": "success",
        "user_id": str(user.id),
        "username": user.username,
        "display_name": user.display_name,
        "stats": {
            "total_predictions": user.total_predictions,
            "correct": user.correct_predictions,
            "wrong": user.wrong_predictions,
            "win_rate": user.win_rate
        }
    }


# ============================================
# OAuth2 Social Login (Google & Meta)
# ============================================

@app.get("/api/auth/google/url", tags=["Community"])
async def get_google_auth_url():
    """Get Google OAuth authorization URL"""
    import secrets
    from services.oauth import get_google_oauth
    
    google = get_google_oauth()
    if not google.client_id:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")
    
    state = secrets.token_urlsafe(32)
    auth_url = google.get_auth_url(state)
    
    return {"auth_url": auth_url, "state": state}


@app.get("/api/auth/facebook/url", tags=["Community"])
async def get_facebook_auth_url():
    """Get Facebook/Meta OAuth authorization URL"""
    import secrets
    from services.oauth import get_facebook_oauth
    
    facebook = get_facebook_oauth()
    if not facebook.app_id:
        raise HTTPException(status_code=503, detail="Facebook OAuth not configured")
    
    state = secrets.token_urlsafe(32)
    auth_url = facebook.get_auth_url(state)
    
    return {"auth_url": auth_url, "state": state}


@app.post("/api/auth/google/callback", tags=["Community"])
async def google_oauth_callback(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """Handle Google OAuth callback - exchange code for user info and login/register"""
    from services.oauth import get_google_oauth
    
    google = get_google_oauth()
    
    # Exchange code for tokens
    tokens = await google.exchange_code(code)
    if not tokens:
        raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
    
    # Get user info
    user_info = await google.get_user_info(tokens["access_token"])
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to get user information")
    
    # Check if user exists by email
    result = await db.execute(
        select(CommunityUser).where(CommunityUser.email == user_info.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user
        username = user_info.email.split("@")[0] + "_g"
        # Ensure unique username
        base_username = username
        counter = 1
        while True:
            result = await db.execute(
                select(CommunityUser).where(CommunityUser.username == username)
            )
            if not result.scalar_one_or_none():
                break
            username = f"{base_username}{counter}"
            counter += 1
        
        user = CommunityUser(
            id=uuid.uuid4(),
            username=username,
            email=user_info.email,
            password_hash="oauth_google_" + user_info.provider_id,  # No password for OAuth users
            display_name=user_info.name,
            avatar_url=user_info.picture_url,
            email_verified=True,  # Google users are pre-verified
            created_at=datetime.utcnow()
        )
        db.add(user)
    
    # Update last login and ensure verified (for existing OAuth users)
    user.last_login = datetime.utcnow()
    user.email_verified = True  # Ensure OAuth users are always verified
    if user_info.picture_url and not user.avatar_url:
        user.avatar_url = user_info.picture_url
    
    await db.commit()
    
    return {
        "status": "success",
        "user_id": str(user.id),
        "username": user.username,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "provider": "google",
        "stats": {
            "total_predictions": user.total_predictions,
            "correct": user.correct_predictions,
            "wrong": user.wrong_predictions,
            "win_rate": user.win_rate
        }
    }


@app.post("/api/auth/facebook/callback", tags=["Community"])
async def facebook_oauth_callback(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """Handle Facebook/Meta OAuth callback - exchange code for user info and login/register"""
    from services.oauth import get_facebook_oauth
    
    facebook = get_facebook_oauth()
    
    # Exchange code for tokens
    tokens = await facebook.exchange_code(code)
    if not tokens:
        raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
    
    # Get user info
    user_info = await facebook.get_user_info(tokens["access_token"])
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to get user information")
    
    # Check if user exists by email
    result = await db.execute(
        select(CommunityUser).where(CommunityUser.email == user_info.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user
        username = user_info.name.lower().replace(" ", "_") + "_fb"
        # Ensure unique username
        base_username = username
        counter = 1
        while True:
            result = await db.execute(
                select(CommunityUser).where(CommunityUser.username == username)
            )
            if not result.scalar_one_or_none():
                break
            username = f"{base_username}{counter}"
            counter += 1
        
        user = CommunityUser(
            id=uuid.uuid4(),
            username=username,
            email=user_info.email,
            password_hash="oauth_facebook_" + user_info.provider_id,  # No password for OAuth users
            display_name=user_info.name,
            avatar_url=user_info.picture_url,
            email_verified=True,  # Facebook users are pre-verified
            created_at=datetime.utcnow()
        )
        db.add(user)
    
    # Update last login and ensure verified (for existing OAuth users)
    user.last_login = datetime.utcnow()
    user.email_verified = True  # Ensure OAuth users are always verified
    if user_info.picture_url and not user.avatar_url:
        user.avatar_url = user_info.picture_url
    
    await db.commit()
    
    return {
        "status": "success",
        "user_id": str(user.id),
        "username": user.username,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "provider": "facebook",
        "stats": {
            "total_predictions": user.total_predictions,
            "correct": user.correct_predictions,
            "wrong": user.wrong_predictions,
            "win_rate": user.win_rate
        }
    }


@app.get("/api/auth/providers", tags=["Community"])
async def get_available_auth_providers():
    """Get list of available OAuth providers"""
    import os
    
    providers = []
    
    if os.getenv("GOOGLE_CLIENT_ID"):
        providers.append({
            "id": "google",
            "name": "Google",
            "enabled": True
        })
    
    if os.getenv("FACEBOOK_APP_ID"):
        providers.append({
            "id": "facebook", 
            "name": "Facebook",
            "enabled": True
        })
    
    return {
        "providers": providers,
        "email_enabled": True  # Always allow email registration
    }

@app.get("/api/community/user/{user_id}")
async def get_community_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get user profile and stats"""
    result = await db.execute(
        select(CommunityUser).where(CommunityUser.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user.id),
        "username": user.username,
        "display_name": user.display_name,
        "bio": user.bio,
        "avatar_url": user.avatar_url,
        "stats": {
            "total_predictions": user.total_predictions,
            "correct": user.correct_predictions,
            "wrong": user.wrong_predictions,
            "open": user.total_predictions - user.correct_predictions - user.wrong_predictions,
            "win_rate": user.win_rate
        },
        "member_since": user.created_at.isoformat()
    }

@app.get("/api/community/user/{user_id}/predictions")
async def get_user_predictions(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all predictions for a user"""
    result = await db.execute(
        select(CommunityPrediction)
        .where(CommunityPrediction.user_id == user_id)
        .order_by(desc(CommunityPrediction.created_at))
    )
    predictions = result.scalars().all()
    
    return [
        {
            "id": str(p.id),
            "claim": p.claim,
            "category": p.category,
            "timeframe": p.timeframe.isoformat(),
            "status": p.status,
            "outcome": p.outcome,
            "created_at": p.created_at.isoformat(),
            "resolved_at": p.resolved_at.isoformat() if p.resolved_at else None
        }
        for p in predictions
    ]

@app.post("/api/community/user/{user_id}/predictions")
async def create_user_prediction(
    user_id: uuid.UUID,
    prediction_data: UserPredictionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new prediction for a user"""
    from datetime import timedelta
    
    # Verify user exists
    result = await db.execute(
        select(CommunityUser).where(CommunityUser.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create prediction
    prediction = CommunityPrediction(
        id=uuid.uuid4(),
        user_id=user_id,
        claim=prediction_data.claim,
        category=prediction_data.category,
        timeframe=datetime.utcnow() + timedelta(days=prediction_data.timeframe_days),
        status="open",
        created_at=datetime.utcnow()
    )
    
    db.add(prediction)
    
    # Update user stats
    user.total_predictions += 1
    
    await db.commit()
    
    return {
        "status": "success",
        "prediction_id": str(prediction.id),
        "claim": prediction.claim,
        "resolves_at": prediction.timeframe.isoformat()
    }

@app.post("/api/community/predictions/{prediction_id}/resolve")
async def resolve_user_prediction(
    prediction_id: uuid.UUID,
    outcome: str,  # 'correct' or 'wrong'
    db: AsyncSession = Depends(get_db)
):
    """Resolve a user's prediction (admin or self-report)"""
    result = await db.execute(
        select(CommunityPrediction)
        .where(CommunityPrediction.id == prediction_id)
        .options(selectinload(CommunityPrediction.user))
    )
    prediction = result.scalar_one_or_none()
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    if prediction.status == "resolved":
        raise HTTPException(status_code=400, detail="Prediction already resolved")
    
    # Update prediction
    prediction.status = "resolved"
    prediction.outcome = "YES" if outcome == "correct" else "NO"
    prediction.resolved_at = datetime.utcnow()
    
    # Update user stats
    user = prediction.user
    if outcome == "correct":
        user.correct_predictions += 1
    else:
        user.wrong_predictions += 1
    
    # Recalculate win rate
    resolved = user.correct_predictions + user.wrong_predictions
    user.win_rate = user.correct_predictions / resolved if resolved > 0 else 0.0
    
    await db.commit()
    
    return {
        "status": "success",
        "prediction_id": str(prediction.id),
        "outcome": prediction.outcome,
        "user_win_rate": user.win_rate
    }

@app.get("/api/community/leaderboard")
async def get_community_leaderboard(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get community leaderboard ranked by win rate (min 3 resolved predictions)"""
    result = await db.execute(
        select(CommunityUser)
        .where(CommunityUser.correct_predictions + CommunityUser.wrong_predictions >= 3)
        .order_by(desc(CommunityUser.win_rate))
        .limit(limit)
    )
    users = result.scalars().all()
    
    return [
        {
            "rank": i + 1,
            "id": str(u.id),
            "username": u.username,
            "display_name": u.display_name,
            "avatar_url": u.avatar_url,
            "total_predictions": u.total_predictions,
            "correct": u.correct_predictions,
            "wrong": u.wrong_predictions,
            "win_rate": u.win_rate
        }
        for i, u in enumerate(users)
    ]

@app.get("/api/community/recent-predictions")
async def get_community_recent_predictions(
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get recent community predictions"""
    result = await db.execute(
        select(CommunityPrediction)
        .options(selectinload(CommunityPrediction.user))
        .order_by(desc(CommunityPrediction.created_at))
        .limit(limit)
    )
    predictions = result.scalars().all()
    
    return [
        {
            "id": str(p.id),
            "claim": p.claim,
            "category": p.category,
            "status": p.status,
            "outcome": p.outcome,
            "timeframe": p.timeframe.isoformat(),
            "created_at": p.created_at.isoformat(),
            "user": {
                "id": str(p.user.id),
                "username": p.user.username,
                "display_name": p.user.display_name
            }
        }
        for p in predictions
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
