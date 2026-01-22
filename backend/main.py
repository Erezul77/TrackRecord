import os
import uuid
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from dotenv import load_dotenv

from database.session import get_db
from database.models import Pundit, PunditMetrics, Prediction, MatchReviewQueue
from schemas import PunditResponse, PredictionResponse, MatchReviewResponse
from pydantic import BaseModel
import hashlib

load_dotenv()

app = FastAPI(
    title="TrackRecord API",
    version="1.0.0",
    description="Pundit prediction tracking and accountability"
)

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

@app.get("/api/leaderboard", response_model=List[PunditResponse])
async def get_leaderboard(
    category: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get leaderboard of pundits ranked by paper_total_pnl
    """
    query = select(Pundit).join(PunditMetrics).options(selectinload(Pundit.metrics))
    
    if category:
        query = query.where(Pundit.domains.any(category))
    
    query = query.order_by(desc(PunditMetrics.paper_total_pnl)).limit(limit)
    
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

@app.get("/api/pundits/{pundit_id}/predictions", response_model=List[PredictionResponse])
async def get_pundit_predictions(pundit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Prediction).where(Prediction.pundit_id == pundit_id).order_by(desc(Prediction.captured_at))
    )
    predictions = result.scalars().all()
    return predictions

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

@app.post("/api/admin/predictions/add")
async def add_manual_prediction(
    prediction_input: ManualPredictionInput,
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Manually add a prediction for a pundit"""
    
    # Find pundit by username
    result = await db.execute(
        select(Pundit).where(Pundit.username == prediction_input.pundit_username)
    )
    pundit = result.scalar_one_or_none()
    
    if not pundit:
        raise HTTPException(status_code=404, detail=f"Pundit '{prediction_input.pundit_username}' not found")
    
    # Create content hash for deduplication
    content_hash = hashlib.sha256(
        f"{prediction_input.quote}{prediction_input.source_url}".encode()
    ).hexdigest()
    
    # Check for duplicate
    existing = await db.execute(
        select(Prediction).where(Prediction.content_hash == content_hash)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="This prediction already exists")
    
    # Calculate timeframe
    from datetime import timedelta
    timeframe = datetime.utcnow() + timedelta(days=prediction_input.timeframe_days)
    
    # Create prediction
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
        captured_at=datetime.utcnow(),
        content_hash=content_hash,
        status="pending",
        flagged=False,
        created_at=datetime.utcnow()
    )
    
    db.add(new_prediction)
    await db.commit()
    
    return {
        "status": "success",
        "prediction_id": str(new_prediction.id),
        "pundit": pundit.name,
        "claim": prediction_input.claim
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
