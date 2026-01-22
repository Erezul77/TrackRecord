import os
import uuid
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
import logging
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

@app.get("/api/pundits/{pundit_id}/predictions", response_model=List[PredictionResponse])
async def get_pundit_predictions(pundit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Prediction).where(Prediction.pundit_id == pundit_id).order_by(desc(Prediction.captured_at))
    )
    predictions = result.scalars().all()
    return predictions

@app.get("/api/predictions/recent")
async def get_recent_predictions(
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get recent predictions from all pundits with pundit info and outcome"""
    from database.models import Position
    
    query = select(Prediction).join(Pundit).options(
        selectinload(Prediction.pundit),
        selectinload(Prediction.positions)
    )
    
    if category:
        query = query.where(Prediction.category == category)
    
    query = query.order_by(desc(Prediction.captured_at)).limit(limit)
    
    result = await db.execute(query)
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
            "outcome": p.positions[0].outcome if p.positions and p.positions[0].outcome else None,
            "pundit": {
                "id": str(p.pundit.id),
                "name": p.pundit.name,
                "username": p.pundit.username,
                "avatar_url": p.pundit.avatar_url
            }
        }
        for p in predictions
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
