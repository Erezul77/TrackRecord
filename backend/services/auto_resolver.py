# services/auto_resolver.py
"""
Auto Resolution Service

Automatically resolves predictions based on:
1. Polymarket market outcomes
2. Time-based deadlines
3. External verification sources
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
import logging

from database.models import Prediction, Match, Position, Pundit, PunditMetrics
from services.polymarket import PolymarketService

logger = logging.getLogger(__name__)


class AutoResolver:
    """Service for automatically resolving predictions"""
    
    def __init__(self):
        self.polymarket = PolymarketService()
    
    async def run_resolution_cycle(self, db: AsyncSession) -> Dict:
        """
        Run a complete resolution cycle.
        Returns summary of what was resolved.
        """
        results = {
            "market_resolved": 0,
            "timeframe_expired": 0,
            "errors": [],
            "details": []
        }
        
        try:
            # 1. Check Polymarket-linked predictions
            market_results = await self._resolve_polymarket_predictions(db)
            results["market_resolved"] = market_results["resolved"]
            results["details"].extend(market_results["details"])
            
            # 2. Check expired timeframe predictions
            expired_results = await self._check_expired_predictions(db)
            results["timeframe_expired"] = expired_results["flagged"]
            results["details"].extend(expired_results["details"])
            
            # 3. Update pundit metrics after resolutions
            if results["market_resolved"] > 0:
                await self._update_pundit_metrics(db)
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error in resolution cycle: {e}")
            results["errors"].append(str(e))
            await db.rollback()
        
        return results
    
    async def _resolve_polymarket_predictions(self, db: AsyncSession) -> Dict:
        """Check Polymarket for resolved markets and update predictions"""
        results = {"resolved": 0, "details": []}
        
        # Get all predictions with active positions (not yet resolved)
        query = (
            select(Prediction)
            .join(Match, Prediction.id == Match.prediction_id)
            .join(Position, Prediction.id == Position.prediction_id)
            .where(Position.status == 'open')
            .options(selectinload(Prediction.match), selectinload(Prediction.position))
        )
        
        result = await db.execute(query)
        predictions = result.scalars().all()
        
        logger.info(f"Checking {len(predictions)} predictions with open positions")
        
        for pred in predictions:
            try:
                if not pred.match:
                    continue
                
                # Fetch current market status from Polymarket
                market = await self.polymarket.get_market_by_id(pred.match.market_id)
                
                if not market:
                    logger.warning(f"Could not fetch market {pred.match.market_id}")
                    continue
                
                # Check if market is resolved (not active and has clear outcome)
                if not market.active:
                    # Market has ended - determine outcome
                    yes_price = market.outcome_prices.get("Yes", 0.5)
                    no_price = market.outcome_prices.get("No", 0.5)
                    
                    # If price is >= 0.95, consider it resolved to that outcome
                    if yes_price >= 0.95:
                        outcome = "YES"
                    elif no_price >= 0.95:
                        outcome = "NO"
                    else:
                        # Market ended but outcome unclear - skip
                        logger.info(f"Market {market.id} ended but outcome unclear (Yes: {yes_price}, No: {no_price})")
                        continue
                    
                    # Update prediction
                    pred.status = "resolved"
                    
                    # Update position
                    if pred.position:
                        pred.position.status = "closed"
                        pred.position.outcome = outcome
                        pred.position.exit_price = yes_price if outcome == "YES" else no_price
                        pred.position.exit_timestamp = datetime.utcnow()
                        
                        # Calculate PnL
                        if pred.position.entry_price and pred.position.shares:
                            if outcome == "YES":
                                # Position was betting on YES
                                pred.position.realized_pnl = (1.0 - pred.position.entry_price) * pred.position.shares
                            else:
                                # Lost the bet
                                pred.position.realized_pnl = -pred.position.entry_price * pred.position.shares
                    
                    results["resolved"] += 1
                    results["details"].append({
                        "prediction_id": str(pred.id),
                        "claim": pred.claim[:100],
                        "outcome": outcome,
                        "market_id": pred.match.market_id
                    })
                    
                    logger.info(f"Resolved prediction {pred.id}: {outcome}")
                
            except Exception as e:
                logger.error(f"Error checking prediction {pred.id}: {e}")
        
        return results
    
    async def _check_expired_predictions(self, db: AsyncSession) -> Dict:
        """Check for predictions whose timeframe has expired"""
        results = {"flagged": 0, "details": []}
        
        now = datetime.utcnow()
        
        # Find predictions with passed timeframes that are still open
        query = (
            select(Prediction)
            .where(
                and_(
                    Prediction.timeframe < now,
                    Prediction.status.in_(['pending_match', 'matched', 'open']),
                    Prediction.flagged == False
                )
            )
        )
        
        result = await db.execute(query)
        predictions = result.scalars().all()
        
        for pred in predictions:
            # Flag for review - don't auto-resolve without market data
            pred.flagged = True
            pred.flag_reason = f"Timeframe expired on {pred.timeframe.isoformat()}. Needs manual resolution."
            
            results["flagged"] += 1
            results["details"].append({
                "prediction_id": str(pred.id),
                "claim": pred.claim[:100],
                "timeframe": pred.timeframe.isoformat(),
                "action": "flagged_for_review"
            })
            
            logger.info(f"Flagged expired prediction {pred.id}")
        
        return results
    
    async def _update_pundit_metrics(self, db: AsyncSession):
        """Update metrics for pundits with newly resolved predictions"""
        # Get all pundits
        result = await db.execute(select(Pundit))
        pundits = result.scalars().all()
        
        for pundit in pundits:
            try:
                # Count predictions
                total_result = await db.execute(
                    select(Prediction).where(Prediction.pundit_id == pundit.id)
                )
                total = len(total_result.scalars().all())
                
                # Count resolved
                resolved_result = await db.execute(
                    select(Position)
                    .join(Prediction, Position.prediction_id == Prediction.id)
                    .where(
                        and_(
                            Prediction.pundit_id == pundit.id,
                            Position.status == 'closed'
                        )
                    )
                )
                resolved_positions = resolved_result.scalars().all()
                
                # Calculate stats
                resolved_count = len(resolved_positions)
                wins = sum(1 for p in resolved_positions if p.outcome == "YES")
                total_pnl = sum(p.realized_pnl or 0 for p in resolved_positions)
                win_rate = (wins / resolved_count * 100) if resolved_count > 0 else 0
                
                # Update or create metrics
                metrics_result = await db.execute(
                    select(PunditMetrics).where(PunditMetrics.pundit_id == pundit.id)
                )
                metrics = metrics_result.scalar_one_or_none()
                
                if not metrics:
                    metrics = PunditMetrics(pundit_id=pundit.id)
                    db.add(metrics)
                
                metrics.total_predictions = total
                metrics.resolved_predictions = resolved_count
                metrics.paper_total_pnl = total_pnl
                metrics.paper_win_rate = win_rate
                metrics.last_calculated = datetime.utcnow()
                
            except Exception as e:
                logger.error(f"Error updating metrics for pundit {pundit.id}: {e}")
    
    async def resolve_single_prediction(
        self, 
        db: AsyncSession, 
        prediction_id: str, 
        outcome: str,
        resolution_notes: str = ""
    ) -> Dict:
        """Manually resolve a single prediction"""
        from uuid import UUID
        
        result = await db.execute(
            select(Prediction)
            .where(Prediction.id == UUID(prediction_id))
            .options(selectinload(Prediction.position))
        )
        pred = result.scalar_one_or_none()
        
        if not pred:
            return {"success": False, "error": "Prediction not found"}
        
        # Update prediction
        pred.status = "resolved"
        pred.flagged = False
        pred.flag_reason = None
        
        # Update position if exists
        if pred.position:
            pred.position.status = "closed"
            pred.position.outcome = outcome
            pred.position.exit_timestamp = datetime.utcnow()
            
            # Calculate PnL based on outcome
            if pred.position.entry_price and pred.position.shares:
                if outcome == "YES":
                    pred.position.realized_pnl = (1.0 - pred.position.entry_price) * pred.position.shares
                else:
                    pred.position.realized_pnl = -pred.position.entry_price * pred.position.shares
        
        await db.commit()
        
        return {
            "success": True,
            "prediction_id": prediction_id,
            "outcome": outcome,
            "notes": resolution_notes
        }
    
    async def close(self):
        await self.polymarket.close()


# Singleton instance
_resolver: Optional[AutoResolver] = None

def get_resolver() -> AutoResolver:
    global _resolver
    if _resolver is None:
        _resolver = AutoResolver()
    return _resolver


async def run_auto_resolution(db: AsyncSession) -> Dict:
    """Convenience function to run auto-resolution"""
    resolver = get_resolver()
    return await resolver.run_resolution_cycle(db)
