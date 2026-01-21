import os
import uuid
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from dotenv import load_dotenv

from database.session import get_db
from database.models import Pundit, PunditMetrics, Prediction, MatchReviewQueue
from schemas import PunditResponse, PredictionResponse, MatchReviewResponse

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
    query = select(Pundit).join(PunditMetrics)
    
    if category:
        query = query.where(Pundit.domains.any(category))
    
    query = query.order_by(desc(PunditMetrics.paper_total_pnl)).limit(limit)
    
    result = await db.execute(query)
    pundits = result.scalars().all()
    return pundits

@app.get("/api/pundits/{pundit_id}", response_model=PunditResponse)
async def get_pundit(pundit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Pundit).where(Pundit.id == pundit_id))
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
