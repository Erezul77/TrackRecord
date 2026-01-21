import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional
import re
from anthropic import Anthropic
from database.models import Prediction, RawContent
import uuid

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """
You are analyzing text to extract specific predictions about future events.

Text to analyze:
---
{text}
---

Author: {author}
Date published: {date}
Source: {source_type}

Extract ALL predictions about future events. A prediction must:
1. Make a claim about something that will/won't happen in the future
2. Be specific enough to verify (not vague like "things will get better")
3. Have a timeframe (explicit or implicit)

For each prediction, provide:
- claim: The specific thing being predicted (as a yes/no question)
- confidence: The author's implied confidence (certain/high/medium/low/speculative)
- timeframe: When this will be verifiable (date, month, year, or "within X months")
- quote: Exact quote from text (verbatim, including context)
- conditionality: Any conditions ("if X then Y") or null
- category: politics/economy/markets/crypto/tech/other

Return ONLY valid JSON array:
[
  {{
    "claim": "Donald Trump will win the 2024 presidential election",
    "confidence": "high",
    "timeframe": "2024-11-05",
    "quote": "Trump is going to win, mark my words. The polling is clear.",
    "conditionality": null,
    "category": "politics"
  }}
]

If no predictions found, return empty array: []

Do NOT include:
- Descriptions of past events
- Vague opinions without specific claims
- Questions posed by author
- Hypotheticals not presented as predictions
"""

class PredictionExtractor:
    def __init__(self):
        self.anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.model = "claude-3-sonnet-20240229"

    async def extract(self, raw_content: RawContent) -> List[Prediction]:
        prompt = EXTRACTION_PROMPT.format(
            text=raw_content.text,
            author="Unknown", # Should be linked to pundit
            date=raw_content.published_at.isoformat(),
            source_type=raw_content.source_type
        )

        try:
            response = self.anthropic.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Claude 3 returns a list of content blocks
            content_text = response.content[0].text
            predictions_json = json.loads(content_text)
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return []

        predictions = []
        for pred_data in predictions_json:
            try:
                prediction = Prediction(
                    id=uuid.uuid4(),
                    pundit_id=raw_content.pundit_id,
                    raw_content_id=raw_content.id,
                    claim=pred_data['claim'],
                    confidence=self._map_confidence(pred_data['confidence']),
                    timeframe=self._parse_timeframe(pred_data['timeframe']),
                    quote=pred_data['quote'],
                    conditionality=pred_data.get('conditionality'),
                    category=pred_data['category'],
                    source_url=raw_content.url or "",
                    source_type=raw_content.source_type,
                    captured_at=datetime.utcnow(),
                    content_hash=self._hash_prediction(raw_content.pundit_id, pred_data['claim'], raw_content.published_at),
                    status='pending_match'
                )
                
                if self._validate(prediction):
                    predictions.append(prediction)
                    
            except Exception as e:
                logger.error(f"Failed to create prediction object: {e}")

        return predictions

    def _map_confidence(self, confidence_str: str) -> float:
        mapping = {
            'certain': 0.95,
            'high': 0.80,
            'medium': 0.60,
            'low': 0.40,
            'speculative': 0.25
        }
        return mapping.get(confidence_str.lower(), 0.50)

    def _parse_timeframe(self, timeframe_str: str) -> datetime:
        try:
            return datetime.fromisoformat(timeframe_str)
        except:
            # Fallback for relative timeframes
            if 'month' in timeframe_str:
                match = re.search(r'\d+', timeframe_str)
                months = int(match.group()) if match else 1
                return datetime.utcnow() + timedelta(days=30 * months)
            if 'year' in timeframe_str:
                match = re.search(r'\d+', timeframe_str)
                years = int(match.group()) if match else 1
                return datetime.utcnow() + timedelta(days=365 * years)
            
            return datetime.utcnow() + timedelta(days=365) # Default 1 year

    def _validate(self, prediction: Prediction) -> bool:
        if not prediction.claim or len(prediction.claim) < 10:
            return False
        if not prediction.quote:
            return False
        return True

    def _hash_prediction(self, pundit_id: uuid.UUID, claim: str, published_at: datetime) -> str:
        content_str = f"{pundit_id}|{claim}|{published_at.isoformat()}"
        return hashlib.sha256(content_str.encode()).hexdigest()
