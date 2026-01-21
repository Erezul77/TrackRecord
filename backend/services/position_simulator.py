import logging
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Position, Match, Prediction

logger = logging.getLogger(__name__)

class PositionSimulator:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    CONFIDENCE_SIZES = {
        0.95: 1000.0,  # Certain
        0.80: 500.0,   # High
        0.60: 300.0,   # Medium
        0.40: 100.0,   # Low
        0.25: 50.0     # Speculative
    }

    def _get_position_size(self, confidence: float) -> float:
        # Find the closest confidence level
        closest_conf = min(self.CONFIDENCE_SIZES.keys(), key=lambda x: abs(x - confidence))
        return self.CONFIDENCE_SIZES[closest_conf]

    async def create_position(self, prediction: Prediction, match: Match) -> Position:
        """
        Create a paper trading position for a matched prediction
        """
        position_size = self._get_position_size(prediction.confidence)
        entry_price = match.entry_price
        
        # Avoid division by zero
        if entry_price <= 0:
            entry_price = 0.01
            
        shares = position_size / entry_price

        position = Position(
            id=uuid.uuid4(),
            prediction_id=prediction.id,
            match_id=match.id,
            pundit_id=prediction.pundit_id,
            market_id=match.market_id,
            market_question=match.market_question,
            entry_price=entry_price,
            entry_timestamp=prediction.captured_at,
            position_size=position_size,
            shares=shares,
            status='open',
            unrealized_pnl=0.0,
            created_at=datetime.utcnow()
        )

        self.db.add(position)
        return position

    async def resolve_position(self, position: Position, outcome: str):
        """
        Resolve a paper trading position (YES or NO)
        """
        if outcome == 'YES':
            exit_price = 1.0
        else:
            exit_price = 0.0
            
        final_value = position.shares * exit_price
        realized_pnl = final_value - position.position_size

        position.status = 'closed'
        position.exit_price = exit_price
        position.exit_timestamp = datetime.utcnow()
        position.realized_pnl = realized_pnl
        position.outcome = outcome
        
        return position
