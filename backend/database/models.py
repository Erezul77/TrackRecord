from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, 
    ForeignKey, Table, UniqueConstraint, Index, JSON, ARRAY
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, BYTEA, ARRAY as PG_ARRAY
import uuid

class Base(DeclarativeBase):
    pass

class Pundit(Base):
    __tablename__ = "pundits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    twitter_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    affiliation: Mapped[Optional[str]] = mapped_column(String(255))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    domains: Mapped[Optional[List[str]]] = mapped_column(PG_ARRAY(String))
    wallet_address: Mapped[Optional[bytes]] = mapped_column(BYTEA)  # Encrypted
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    last_tweet_id: Mapped[Optional[str]] = mapped_column(String(50))
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    predictions = relationship("Prediction", back_populates="pundit")
    metrics = relationship("PunditMetrics", back_populates="pundit", uselist=False)

class RawContent(Base):
    __tablename__ = "raw_content"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pundit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pundits.id"))
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # twitter, podcast, article
    text: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(1000))
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pundit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pundits.id"), nullable=False)
    raw_content_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("raw_content.id"))
    
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    timeframe: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    quote: Mapped[str] = mapped_column(Text, nullable=False)
    conditionality: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_type: Mapped[Optional[str]] = mapped_column(String(50))
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    
    status: Mapped[str] = mapped_column(String(50), default='pending_match')
    matched_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    flag_reason: Mapped[Optional[str]] = mapped_column(Text)
    verified_by_pundit: Mapped[Optional[bool]] = mapped_column(Boolean)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    pundit = relationship("Pundit", back_populates="predictions")
    match = relationship("Match", back_populates="prediction", uselist=False)
    position = relationship("Position", back_populates="prediction", uselist=False)

class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("predictions.id"), nullable=False, unique=True)
    
    market_id: Mapped[str] = mapped_column(String(100), nullable=False)
    market_slug: Mapped[Optional[str]] = mapped_column(String(255))
    market_question: Mapped[str] = mapped_column(Text, nullable=False)
    market_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    match_type: Mapped[str] = mapped_column(String(50), nullable=False)
    alternatives: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    entry_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    matched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    prediction = relationship("Prediction", back_populates="match")

class Position(Base):
    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("predictions.id"), nullable=False)
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id"), nullable=False)
    pundit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pundits.id"), nullable=False)
    
    market_id: Mapped[str] = mapped_column(String(100), nullable=False)
    market_question: Mapped[str] = mapped_column(Text, nullable=False)
    
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    entry_timestamp: Mapped[datetime] = mapped_column(DateTime)
    position_size: Mapped[float] = mapped_column(Float, nullable=False)
    shares: Mapped[float] = mapped_column(Float, nullable=False)
    
    status: Mapped[str] = mapped_column(String(50), default='open')
    current_price: Mapped[Optional[float]] = mapped_column(Float)
    unrealized_pnl: Mapped[Optional[float]] = mapped_column(Float)
    
    exit_price: Mapped[Optional[float]] = mapped_column(Float)
    exit_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    realized_pnl: Mapped[Optional[float]] = mapped_column(Float)
    outcome: Mapped[Optional[str]] = mapped_column(String(10))
    
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    prediction = relationship("Prediction", back_populates="position")

class PunditMetrics(Base):
    __tablename__ = "pundit_metrics"

    pundit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pundits.id"), primary_key=True)
    
    total_predictions: Mapped[int] = mapped_column(Integer, default=0)
    matched_predictions: Mapped[int] = mapped_column(Integer, default=0)
    resolved_predictions: Mapped[int] = mapped_column(Integer, default=0)
    
    paper_total_pnl: Mapped[float] = mapped_column(Float, default=0)
    paper_win_rate: Mapped[float] = mapped_column(Float, default=0)
    paper_roi: Mapped[float] = mapped_column(Float, default=0)
    paper_sharpe_ratio: Mapped[Optional[float]] = mapped_column(Float)
    paper_max_drawdown: Mapped[Optional[float]] = mapped_column(Float)
    
    real_total_pnl: Mapped[Optional[float]] = mapped_column(Float)
    real_win_rate: Mapped[Optional[float]] = mapped_column(Float)
    real_roi: Mapped[Optional[float]] = mapped_column(Float)
    
    metrics_by_category: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    pnl_30d: Mapped[Optional[float]] = mapped_column(Float)
    pnl_90d: Mapped[Optional[float]] = mapped_column(Float)
    pnl_365d: Mapped[Optional[float]] = mapped_column(Float)
    
    global_rank: Mapped[Optional[int]] = mapped_column(Integer)
    category_ranks: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    last_calculated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    pundit = relationship("Pundit", back_populates="metrics")

class MatchReviewQueue(Base):
    __tablename__ = "match_review_queue"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("predictions.id"), nullable=False)
    suggested_market_id: Mapped[str] = mapped_column(String(100), nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='pending') # pending, approved, rejected
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    prediction = relationship("Prediction")


# ============================================
# Community Competition - User Predictions
# ============================================

class CommunityUser(Base):
    """Users who participate in the prediction competition"""
    __tablename__ = "community_users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    
    # Stats (denormalized for performance)
    total_predictions: Mapped[int] = mapped_column(Integer, default=0)
    correct_predictions: Mapped[int] = mapped_column(Integer, default=0)
    wrong_predictions: Mapped[int] = mapped_column(Integer, default=0)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    predictions = relationship("CommunityPrediction", back_populates="user")


class CommunityPrediction(Base):
    """Predictions made by community users"""
    __tablename__ = "community_predictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("community_users.id"), nullable=False)
    
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default='general')
    timeframe: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # When it should resolve
    
    # Outcome
    status: Mapped[str] = mapped_column(String(20), default='open')  # open, resolved
    outcome: Mapped[Optional[str]] = mapped_column(String(10))  # YES (correct), NO (wrong)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    user = relationship("CommunityUser", back_populates="predictions")
