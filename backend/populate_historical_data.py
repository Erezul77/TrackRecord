# populate_historical_data.py
# Seeds the database with historical pundit data using simulator standards

import asyncio
import json
import uuid
import hashlib
from datetime import datetime
from pathlib import Path

from database.session import async_session
from database.models import Pundit, PunditMetrics, Prediction, Match, Position

# Simulator confidence to position size mapping (from architecture)
CONFIDENCE_TO_SIZE = {
    0.95: 1000.0,  # Certain
    0.80: 500.0,   # High
    0.60: 300.0,   # Medium
    0.40: 100.0,   # Low
    0.25: 50.0     # Speculative
}

CONFIDENCE_MAP = {
    "certain": 0.95,
    "high": 0.80,
    "medium": 0.60,
    "low": 0.40,
    "speculative": 0.25
}

def get_position_size(confidence: float) -> float:
    """Map confidence to position size per simulator standards"""
    closest = min(CONFIDENCE_TO_SIZE.keys(), key=lambda x: abs(x - confidence))
    return CONFIDENCE_TO_SIZE[closest]

def calculate_pnl(position_size: float, entry_price: float, resolution_price: float) -> float:
    """Calculate P&L using simulator logic"""
    if entry_price <= 0:
        entry_price = 0.01
    
    shares = position_size / entry_price
    
    if resolution_price is None:
        # Pending - estimate current price as 0.5 (unknown)
        return 0.0
    
    final_value = shares * resolution_price
    return final_value - position_size

def hash_prediction(pundit_name: str, claim: str, date: str) -> str:
    """Generate unique hash for prediction"""
    content = f"{pundit_name}|{claim}|{date}"
    return hashlib.sha256(content.encode()).hexdigest()

async def populate():
    print("=" * 60)
    print("TrackRecord Historical Data Population")
    print("Using Simulator Standards")
    print("=" * 60)
    
    # Load historical data
    data_path = Path(__file__).parent / "historical_data" / "pundits.json"
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"\nLoaded {len(data['pundits'])} pundits from historical data\n")
    
    async with async_session() as session:
        for pundit_data in data["pundits"]:
            print(f"Processing: {pundit_data['name']}")
            
            # Create Pundit
            pundit_id = uuid.uuid4()
            pundit = Pundit(
                id=pundit_id,
                name=pundit_data["name"],
                username=pundit_data["username"],
                twitter_id=pundit_data.get("twitter_id"),
                affiliation=pundit_data["affiliation"],
                bio=pundit_data["bio"],
                avatar_url=pundit_data.get("avatar_url"),
                domains=pundit_data["domains"],
                verified=True,
                verified_at=datetime.utcnow()
            )
            session.add(pundit)
            
            # Track metrics
            total_predictions = 0
            resolved_predictions = 0
            wins = 0
            total_pnl = 0.0
            total_invested = 0.0
            
            # Process predictions
            for pred_data in pundit_data["predictions"]:
                total_predictions += 1
                
                confidence = CONFIDENCE_MAP.get(pred_data["confidence"], 0.60)
                position_size = get_position_size(confidence)
                entry_price = pred_data.get("entry_price_estimate", 0.50)
                resolution_price = pred_data.get("resolution_price")
                
                # Calculate P&L
                if pred_data["outcome"] not in ["pending"]:
                    resolved_predictions += 1
                    pnl = calculate_pnl(position_size, entry_price, resolution_price or 0.0)
                    total_pnl += pnl
                    total_invested += position_size
                    
                    if pred_data["outcome"] == "right":
                        wins += 1
                    elif pred_data["outcome"] == "partially":
                        wins += 0.5
                
                # Create Prediction
                pred_id = uuid.uuid4()
                prediction = Prediction(
                    id=pred_id,
                    pundit_id=pundit_id,
                    claim=pred_data["claim"],
                    confidence=confidence,
                    timeframe=datetime.fromisoformat(pred_data["timeframe"]),
                    quote=pred_data["quote"],
                    category=pred_data["category"],
                    source_url=pred_data["source_url"],
                    source_type=pred_data["source_type"],
                    captured_at=datetime.fromisoformat(pred_data["date"]),
                    content_hash=hash_prediction(pundit_data["name"], pred_data["claim"], pred_data["date"]),
                    status="resolved" if pred_data["outcome"] != "pending" else "matched"
                )
                session.add(prediction)
                
                # Create Match (simulated market)
                match_id = uuid.uuid4()
                match = Match(
                    id=match_id,
                    prediction_id=pred_id,
                    market_id=f"historical-{pred_id}",
                    market_slug=f"historical-{pred_data['category']}-{pred_data['date']}",
                    market_question=pred_data["claim"],
                    similarity_score=0.95,  # Historical = perfect match
                    match_type="historical",
                    entry_price=entry_price,
                    entry_timestamp=datetime.fromisoformat(pred_data["date"])
                )
                session.add(match)
                
                # Create Position
                shares = position_size / entry_price if entry_price > 0 else 0
                realized_pnl = None
                unrealized_pnl = None
                status = "open"
                exit_price = None
                outcome = None
                
                if pred_data["outcome"] != "pending":
                    status = "closed"
                    exit_price = resolution_price or 0.0
                    realized_pnl = calculate_pnl(position_size, entry_price, exit_price)
                    outcome = "YES" if pred_data["outcome"] in ["right", "partially"] else "NO"
                else:
                    unrealized_pnl = 0.0
                
                position = Position(
                    id=uuid.uuid4(),
                    prediction_id=pred_id,
                    match_id=match_id,
                    pundit_id=pundit_id,
                    market_id=match.market_id,
                    market_question=pred_data["claim"],
                    entry_price=entry_price,
                    entry_timestamp=datetime.fromisoformat(pred_data["date"]),
                    position_size=position_size,
                    shares=shares,
                    status=status,
                    current_price=resolution_price,
                    unrealized_pnl=unrealized_pnl,
                    exit_price=exit_price,
                    realized_pnl=realized_pnl,
                    outcome=outcome
                )
                session.add(position)
            
            # Calculate metrics
            win_rate = (wins / resolved_predictions) if resolved_predictions > 0 else 0.0
            roi = (total_pnl / total_invested) if total_invested > 0 else 0.0
            
            # Create PunditMetrics
            metrics = PunditMetrics(
                pundit_id=pundit_id,
                total_predictions=total_predictions,
                matched_predictions=total_predictions,
                resolved_predictions=resolved_predictions,
                paper_total_pnl=round(total_pnl, 2),
                paper_win_rate=round(win_rate, 3),
                paper_roi=round(roi, 3),
                pnl_30d=round(total_pnl * 0.15, 2),  # Estimate recent as 15%
                pnl_90d=round(total_pnl * 0.35, 2),
                pnl_365d=round(total_pnl * 0.70, 2),
                global_rank=None  # Will be calculated after all pundits
            )
            session.add(metrics)
            
            print(f"  ├── Predictions: {total_predictions}")
            print(f"  ├── Resolved: {resolved_predictions}")
            print(f"  ├── Win Rate: {win_rate:.1%}")
            print(f"  └── Total P&L: ${total_pnl:,.2f}")
            print()
        
        await session.commit()
        
        # Update global rankings
        print("Calculating global rankings...")
        from sqlalchemy import select, desc
        
        result = await session.execute(
            select(PunditMetrics).order_by(desc(PunditMetrics.paper_total_pnl))
        )
        all_metrics = result.scalars().all()
        
        for rank, metrics in enumerate(all_metrics, 1):
            metrics.global_rank = rank
        
        await session.commit()
        
    print("=" * 60)
    print("Historical data population complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(populate())
