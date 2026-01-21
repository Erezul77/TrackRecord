from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import uuid

class MetricsResponse(BaseModel):
    total_predictions: int
    resolved_predictions: int
    paper_total_pnl: float
    paper_win_rate: float
    paper_roi: float
    real_total_pnl: Optional[float] = None
    pnl_30d: Optional[float] = 0.0
    global_rank: Optional[int] = None

class PunditResponse(BaseModel):
    id: uuid.UUID
    name: str
    username: Optional[str] = None
    affiliation: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    domains: List[str] = []
    verified: bool
    metrics: Optional[MetricsResponse] = None

    class Config:
        from_attributes = True

class PredictionResponse(BaseModel):
    id: uuid.UUID
    pundit_id: uuid.UUID
    claim: str
    confidence: float
    timeframe: datetime
    quote: str
    category: str
    source_url: str
    captured_at: datetime
    status: str
    
    class Config:
        from_attributes = True

class MatchReviewResponse(BaseModel):
    id: uuid.UUID
    prediction_id: uuid.UUID
    suggested_market_id: str
    similarity_score: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
