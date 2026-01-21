import os
import logging
import numpy as np
from typing import Optional, List, Tuple
from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Prediction, Match
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class MarketMatcher:
    def __init__(self, db_session: AsyncSession):
        self.openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.db = db_session

    async def get_embedding(self, text: str) -> List[float]:
        response = self.openai.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    async def find_matches(self, prediction: Prediction) -> List[Tuple[dict, float]]:
        """
        Find matching markets in Polymarket using pgvector semantic search
        """
        prediction_embedding = await self.get_embedding(prediction.claim)
        
        # Query market_cache table using vector similarity
        # We'll use cosine distance (<=> operator in pgvector)
        query = text("""
            SELECT market_id, market_slug, question, end_date, current_price,
                   (embedding <=> :embedding) as distance
            FROM market_cache
            WHERE closed = False
            ORDER BY distance ASC
            LIMIT 5
        """)
        
        result = await self.db.execute(query, {"embedding": str(prediction_embedding)})
        matches = []
        for row in result:
            # distance is 1 - cosine_similarity, so similarity is 1 - distance
            similarity = 1 - float(row.distance)
            matches.append(({
                "market_id": row.market_id,
                "market_slug": row.market_slug,
                "question": row.question,
                "end_date": row.end_date,
                "current_price": row.current_price
            }, similarity))
            
        return matches

    async def create_match(self, prediction: Prediction) -> Optional[Match]:
        matches = await self.find_matches(prediction)
        
        if not matches:
            return None
            
        best_market, similarity = matches[0]
        
        # Thresholds from architecture
        if similarity > 0.85:
            match_type = 'auto_matched'
        elif similarity > 0.70:
            match_type = 'needs_review'
        else:
            return None

        match = Match(
            id=uuid.uuid4(),
            prediction_id=prediction.id,
            market_id=best_market['market_id'],
            market_slug=best_market['market_slug'],
            market_question=best_market['question'],
            market_end_date=best_market['end_date'],
            similarity_score=similarity,
            match_type=match_type,
            entry_price=best_market['current_price'] or 0.5, # Default if price missing
            entry_timestamp=datetime.utcnow(),
            alternatives=[m[0] for m in matches[1:]]
        )
        
        self.db.add(match)
        return match
