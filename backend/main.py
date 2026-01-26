import os
import uuid
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
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
async def health_check():
    return {"status": "healthy"}

# Auto-start scheduler on startup (controlled by env var)
@app.on_event("startup")
async def startup_event():
    auto_start = os.getenv("AUTO_START_SCHEDULER", "false").lower() == "true"
    if auto_start:
        from services.scheduler import start_scheduler
        try:
            scheduler = start_scheduler()
            logging.info("Background scheduler auto-started")
        except Exception as e:
            logging.error(f"Failed to start scheduler: {e}")

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
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all pundits. Frontend handles showing 'needs more data' for < 3 resolved.
    Ranked by win rate (accuracy).
    """
    query = select(Pundit).join(PunditMetrics).options(selectinload(Pundit.metrics))
    
    if category:
        query = query.where(Pundit.domains.any(category))
    
    # Show everyone, ranked by win rate
    # Those with < 3 resolved will show "needs more data" in frontend
    query = query.order_by(desc(PunditMetrics.paper_win_rate)).limit(limit)
    
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

@app.get("/api/pundits/{pundit_id}/predictions")
async def get_pundit_predictions(pundit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get all predictions for a pundit with outcome status"""
    result = await db.execute(
        select(Prediction)
        .where(Prediction.pundit_id == pundit_id)
        .options(selectinload(Prediction.position))
        .order_by(desc(Prediction.captured_at))
    )
    predictions = result.scalars().all()
    
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
            "outcome": p.position.outcome if p.position and p.position.outcome else None,
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
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = None,
    sort: str = Query("default", description="Sort: default, newest, oldest, resolving_soon, boldest, highest_score"),
    db: AsyncSession = Depends(get_db)
):
    """Get recent predictions from all pundits with pundit info and outcome"""
    from database.models import Position
    
    query = select(Prediction).join(Pundit).options(
        selectinload(Prediction.pundit),
        selectinload(Prediction.position)
    )
    
    if category:
        query = query.where(Prediction.category == category)
    
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
            has_outcome = p.position and p.position.outcome
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
            has_outcome = p.position and p.position.outcome
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
            "outcome": p.position.outcome if p.position and p.position.outcome else None,
            "tr_index": {
                "score": p.tr_index_score,
                "tier": "gold" if p.tr_index_score and p.tr_index_score >= 80 else 
                        "silver" if p.tr_index_score and p.tr_index_score >= 60 else 
                        "bronze" if p.tr_index_score and p.tr_index_score >= 40 else None
            } if p.tr_index_score else None,
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
    Accept crowdsourced historical prediction submissions.
    These are stored for review before being added to the main database.
    """
    import json
    from pathlib import Path
    
    # Store submissions in a JSON file for review
    submissions_file = Path(__file__).parent / "crowdsourced_submissions.json"
    
    try:
        if submissions_file.exists():
            with open(submissions_file, "r") as f:
                submissions = json.load(f)
        else:
            submissions = []
        
        # Add new submission
        submissions.append({
            "id": str(uuid.uuid4()),
            "submitted_at": datetime.utcnow().isoformat(),
            "status": "pending_review",
            **submission.dict()
        })
        
        with open(submissions_file, "w") as f:
            json.dump(submissions, f, indent=2)
        
        logging.info(f"New prediction submission: {submission.pundit_name} - {submission.claim[:50]}")
        
        return {
            "status": "success",
            "message": "Submission received and queued for review"
        }
        
    except Exception as e:
        logging.error(f"Failed to save submission: {e}")
        raise HTTPException(status_code=500, detail="Failed to save submission")


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
        .where(Prediction.timeframe <= now)  # Past deadline
        .where(Prediction.status != 'resolved')  # Not yet resolved
        .where(
            or_(
                Position.id == None,  # No position
                Position.outcome == None  # Position exists but no outcome
            )
        )
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
    """Get all predictions pending manual verification (no Polymarket match or unresolved)"""
    from sqlalchemy import or_
    
    # Get predictions that are either:
    # 1. pending_match (no Polymarket match found)
    # 2. matched but not yet resolved
    result = await db.execute(
        select(Prediction, Pundit)
        .join(Pundit, Prediction.pundit_id == Pundit.id)
        .outerjoin(Position, Position.prediction_id == Prediction.id)
        .where(
            or_(
                Prediction.status == 'pending_match',
                Prediction.status == 'matched'
            )
        )
        .where(
            or_(
                Position.id == None,  # No position (unmatched)
                Position.outcome == None  # Position exists but no outcome
            )
        )
        .order_by(Prediction.timeframe.asc())  # Soonest deadline first
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


# ============================================
# Prediction Voting System
# ============================================

class VoteInput(BaseModel):
    user_id: str
    vote_type: str  # 'up' or 'down'

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

@app.post("/api/community/register")
async def register_user(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register a new community user"""
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
    
    # Create user
    user = CommunityUser(
        id=uuid.uuid4(),
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        display_name=user_data.display_name or user_data.username,
        created_at=datetime.utcnow()
    )
    
    db.add(user)
    await db.commit()
    
    return {
        "status": "success",
        "user_id": str(user.id),
        "username": user.username,
        "message": "Registration successful! You can now log in."
    }

@app.post("/api/community/login")
async def login_user(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login and get user session"""
    result = await db.execute(
        select(CommunityUser).where(CommunityUser.email == login_data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
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
