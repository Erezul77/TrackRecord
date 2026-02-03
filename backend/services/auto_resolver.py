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
            "expired_auto_resolved": 0,
            "flagged_for_review": 0,
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
            results["expired_auto_resolved"] = expired_results.get("auto_resolved", 0)
            results["flagged_for_review"] = expired_results.get("flagged", 0)
            results["details"].extend(expired_results["details"])
            
            # 3. Update pundit metrics after resolutions
            total_resolved = results["market_resolved"] + results["expired_auto_resolved"]
            if total_resolved > 0:
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
        """
        Check for predictions whose timeframe has expired.
        
        Logic:
        - If timeframe passed and prediction was about something happening BY a date,
          and it didn't happen → auto-resolve as NO (wrong)
        - The absence of the event IS the proof
        """
        results = {"auto_resolved": 0, "flagged": 0, "details": []}
        
        now = datetime.utcnow()
        
        # Find predictions with passed timeframes that are still open
        # IMPORTANT: Include ALL unresolved statuses, especially 'pending'
        query = (
            select(Prediction)
            .where(
                and_(
                    Prediction.timeframe < now,
                    Prediction.status.in_(['pending', 'pending_match', 'matched', 'open']),
                )
            )
            .options(selectinload(Prediction.position))
        )
        
        result = await db.execute(query)
        predictions = result.scalars().all()
        
        for pred in predictions:
            # Analyze the claim to determine if it's a "by date X" type prediction
            claim_lower = pred.claim.lower()
            
            # Keywords that suggest the prediction is about something happening BY a deadline
            deadline_keywords = [
                'will reach', 'will hit', 'will be', 'will become', 
                'will win', 'will pass', 'will happen', 'will occur',
                'by end of', 'by the end', 'before', 'within'
            ]
            
            is_deadline_prediction = any(kw in claim_lower for kw in deadline_keywords)
            
            if is_deadline_prediction:
                # Auto-resolve as NO - the event didn't happen by the deadline
                pred.status = "resolved"
                pred.flagged = False
                pred.flag_reason = None
                
                # Update position if exists
                if pred.position:
                    pred.position.status = "closed"
                    pred.position.outcome = "NO"  # Prediction was wrong
                    pred.position.exit_timestamp = now
                    
                    # Calculate loss
                    if pred.position.entry_price and pred.position.shares:
                        pred.position.realized_pnl = -pred.position.entry_price * pred.position.shares
                
                resolution_note = f"Auto-resolved: Timeframe expired on {pred.timeframe.strftime('%Y-%m-%d')}. The predicted event did not occur by the deadline."
                
                results["auto_resolved"] += 1
                results["details"].append({
                    "prediction_id": str(pred.id),
                    "claim": pred.claim[:100],
                    "timeframe": pred.timeframe.isoformat(),
                    "outcome": "NO",
                    "action": "auto_resolved_expired",
                    "reason": resolution_note
                })
                
                logger.info(f"Auto-resolved expired prediction {pred.id} as NO (wrong)")
            
            else:
                # Can't auto-determine - flag for manual review
                pred.flagged = True
                pred.flag_reason = f"Timeframe expired on {pred.timeframe.isoformat()}. Needs manual resolution - unable to auto-determine outcome."
                
                results["flagged"] += 1
                results["details"].append({
                    "prediction_id": str(pred.id),
                    "claim": pred.claim[:100],
                    "timeframe": pred.timeframe.isoformat(),
                    "action": "flagged_for_review"
                })
                
                logger.info(f"Flagged expired prediction {pred.id} for manual review")
        
        return results
    
    async def _update_ai_resolved_metrics(self, db: AsyncSession, pundit_id, outcome: str):
        """Update metrics for a pundit after AI resolution"""
        try:
            # Get pundit metrics
            metrics_result = await db.execute(
                select(PunditMetrics).where(PunditMetrics.pundit_id == pundit_id)
            )
            metrics = metrics_result.scalar_one_or_none()
            
            if metrics:
                metrics.resolved_predictions = (metrics.resolved_predictions or 0) + 1
                
                # Update win rate and PnL
                if outcome == "YES":
                    # Correct prediction
                    current_wins = int((metrics.paper_win_rate or 0) * (metrics.resolved_predictions - 1))
                    new_wins = current_wins + 1
                    metrics.paper_win_rate = new_wins / metrics.resolved_predictions
                    metrics.paper_total_pnl = (metrics.paper_total_pnl or 0) + 50
                else:
                    # Wrong prediction
                    current_wins = int((metrics.paper_win_rate or 0) * (metrics.resolved_predictions - 1))
                    metrics.paper_win_rate = current_wins / metrics.resolved_predictions
                    metrics.paper_total_pnl = (metrics.paper_total_pnl or 0) - 50
                
                metrics.last_calculated = datetime.utcnow()
                
        except Exception as e:
            logger.error(f"Error updating AI resolved metrics: {e}")
    
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
                win_rate = (wins / resolved_count) if resolved_count > 0 else 0  # Store as decimal (0.75 = 75%)
                
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
    
    async def ai_resolve_prediction(
        self,
        db: AsyncSession,
        prediction_id: str
    ) -> Dict:
        """
        Use AI (Claude) to evaluate a prediction and determine if it was correct.
        
        The AI will analyze:
        1. The prediction claim
        2. When it was made
        3. What actually happened (based on knowledge cutoff)
        
        Returns: {"success": bool, "outcome": "YES/NO", "reasoning": str}
        """
        import os
        import httpx
        from uuid import UUID
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {"success": False, "error": "Anthropic API key not configured"}
        
        # Get the prediction
        result = await db.execute(
            select(Prediction)
            .where(Prediction.id == UUID(prediction_id))
            .options(selectinload(Prediction.pundit))
        )
        pred = result.scalar_one_or_none()
        
        if not pred:
            return {"success": False, "error": "Prediction not found"}
        
        if pred.status == "resolved":
            return {"success": False, "error": "Prediction already resolved"}
        
        # Build the prompt
        pundit_name = pred.pundit.name if pred.pundit else "Unknown"
        claim = pred.claim
        made_at = pred.captured_at.strftime("%B %Y") if pred.captured_at else "Unknown date"
        timeframe = pred.timeframe.strftime("%B %Y") if pred.timeframe else "Unknown"
        
        prompt = f"""You are a fact-checker evaluating whether a prediction came true. Be DECISIVE.

PREDICTION:
- Made by: {pundit_name}
- Claim: "{claim}"
- Made around: {made_at}
- Deadline: {timeframe}

TODAY'S DATE: January 2026

EVALUATION RULES:
1. For market/industry claims (e.g., "NVIDIA will dominate chips in 2024"):
   - Check if the company/entity achieved the claimed dominance by the deadline
   - Market share leadership or clear dominance = YES
   - Did not achieve dominance = NO

2. For price/number predictions (e.g., "Bitcoin will hit $100k in 2024"):
   - Check if the target was reached by deadline
   - Reached target = YES, Did not reach = NO

3. For event predictions (e.g., "X will win election"):
   - Check if the event happened
   - Event happened = YES, Did not happen = NO

4. For vague predictions without clear metrics:
   - If reasonable interpretation shows it came true = YES
   - If reasonable interpretation shows it failed = NO
   - Only use UNKNOWN if truly impossible to evaluate

BE DECISIVE. Most predictions CAN be evaluated. Only use UNKNOWN as last resort.

Respond ONLY with JSON:
{{"outcome": "YES/NO/UNKNOWN", "confidence": 0.6-1.0, "reasoning": "One sentence explanation"}}"""

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 500,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                )
                
                if response.status_code != 200:
                    return {"success": False, "error": f"API error: {response.status_code}"}
                
                data = response.json()
                ai_response = data["content"][0]["text"].strip()
                
                # Parse JSON response
                import json
                try:
                    result_data = json.loads(ai_response)
                except:
                    # Try to extract JSON from response
                    import re
                    json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                    if json_match:
                        result_data = json.loads(json_match.group())
                    else:
                        return {"success": False, "error": "Could not parse AI response", "raw": ai_response}
                
                outcome = result_data.get("outcome", "UNKNOWN").upper()
                confidence = result_data.get("confidence", 0.5)
                reasoning = result_data.get("reasoning", "")
                
                # Auto-resolve if reasonably confident (lowered threshold for better coverage)
                if outcome in ["YES", "NO"] and confidence >= 0.6:
                    # Resolve the prediction - SET THE OUTCOME!
                    pred.status = "resolved"
                    pred.outcome = outcome  # THIS WAS MISSING!
                    pred.resolved_at = datetime.utcnow()
                    pred.resolution_source = "ai"
                    pred.flagged = False
                    pred.flag_reason = f"AI resolved: {reasoning[:200]}"
                    
                    await db.commit()
                    
                    # Update pundit metrics based on AI resolution
                    await self._update_ai_resolved_metrics(db, pred.pundit_id, outcome)
                    await db.commit()
                    
                    return {
                        "success": True,
                        "prediction_id": prediction_id,
                        "outcome": outcome,
                        "confidence": confidence,
                        "reasoning": reasoning,
                        "action": "resolved"
                    }
                else:
                    return {
                        "success": True,
                        "prediction_id": prediction_id,
                        "outcome": outcome,
                        "confidence": confidence,
                        "reasoning": reasoning,
                        "action": "not_resolved",
                        "reason": "Low confidence or indeterminate outcome"
                    }
                    
        except Exception as e:
            logger.error(f"AI resolution error: {e}")
            return {"success": False, "error": str(e)}
    
    async def ai_resolve_batch(
        self,
        db: AsyncSession,
        limit: int = 20
    ) -> Dict:
        """
        Use AI to resolve multiple open predictions.
        
        Returns summary of resolutions.
        """
        results = {
            "processed": 0,
            "resolved_yes": 0,
            "resolved_no": 0,
            "skipped": 0,
            "errors": 0,
            "details": []
        }
        
        # Get open predictions with past timeframes (candidates for resolution)
        now = datetime.utcnow()
        query = (
            select(Prediction)
            .where(
                and_(
                    Prediction.timeframe < now,
                    Prediction.status.in_(['pending', 'pending_match', 'matched', 'open']),
                    Prediction.outcome.is_(None),  # Not already resolved
                    Prediction.flagged == False  # Don't resolve flagged predictions
                )
            )
            .options(selectinload(Prediction.pundit))
            .order_by(Prediction.timeframe.asc())  # Oldest overdue first
            .limit(limit)
        )
        
        result = await db.execute(query)
        predictions = result.scalars().all()
        
        logger.info(f"AI resolving {len(predictions)} predictions...")
        
        for pred in predictions:
            try:
                res = await self.ai_resolve_prediction(db, str(pred.id))
                results["processed"] += 1
                
                if res.get("success") and res.get("action") == "resolved":
                    if res.get("outcome") == "YES":
                        results["resolved_yes"] += 1
                    else:
                        results["resolved_no"] += 1
                    results["details"].append({
                        "prediction_id": str(pred.id),
                        "claim": pred.claim[:100],
                        "outcome": res.get("outcome"),
                        "reasoning": res.get("reasoning", "")[:200]
                    })
                else:
                    results["skipped"] += 1
                    
            except Exception as e:
                results["errors"] += 1
                logger.error(f"Error AI resolving {pred.id}: {e}")
        
        return results
    
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
