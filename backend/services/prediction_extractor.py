# services/prediction_extractor.py
# AI-powered prediction extraction using Claude

import os
import json
import httpx
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


@dataclass
class ExtractedPrediction:
    """A prediction extracted from an article"""
    pundit_name: str
    pundit_username: Optional[str]
    claim: str
    quote: str
    timeframe_description: str
    timeframe_days: int
    category: str
    specificity: int  # 1-5
    verifiability: int  # 1-5
    boldness: int  # 1-5
    stakes: int  # 1-5
    confidence_in_extraction: float  # How confident we are this is a real prediction


EXTRACTION_PROMPT = """You are an expert at identifying specific, measurable predictions from financial news articles.

Analyze the following article and extract any SPECIFIC, MEASURABLE predictions made by named individuals.

RULES FOR VALID PREDICTIONS:
1. Must be made by a NAMED person (not "analysts" or "experts")
2. Must be SPECIFIC and MEASURABLE (not vague opinions)
3. Must have a TIMEFRAME (explicit or implied)
4. Must be VERIFIABLE with public data when the time comes

INVALID examples (do NOT extract):
- "Markets could be volatile" (too vague)
- "Experts predict growth" (no named person)
- "Things might improve" (not measurable)

VALID examples:
- "Ray Dalio predicts US dollar will lose reserve currency status within 5 years"
- "Cathie Wood says Bitcoin will reach $1 million by 2030"
- "Jamie Dimon warns of 50% stock market correction in next 18 months"

For each valid prediction found, provide:
1. pundit_name: Full name of the person making the prediction
2. pundit_username: Twitter/X handle if known (without @), or null
3. claim: Clear, concise statement of the prediction
4. quote: The exact or near-exact quote from the article
5. timeframe_description: When they expect this to happen (e.g., "by end of 2026", "within 5 years")
6. timeframe_days: Estimated days from today until resolution (e.g., 365 for "1 year")
7. category: One of: crypto, markets, economy, politics, tech, macro, sports, entertainment, religion, science, business, media, health, climate, geopolitics, us, uk, eu, china, japan, india, israel, russia, brazil, latam, middle-east, africa, asia-pacific
8. specificity: 1-5 (1=vague, 5=very specific with numbers/dates)
9. verifiability: 1-5 (1=hard to verify, 5=easily verified with public data)
10. boldness: 1-5 (1=consensus view, 5=very contrarian)
11. stakes: 1-5 (1=minor, 5=major market/world impact)
12. confidence_in_extraction: 0.0-1.0 (how confident you are this is a real, valid prediction)

ARTICLE:
Title: {title}
Source: {source}
Published: {published}
Content: {content}

Respond with a JSON array of predictions. If no valid predictions found, return an empty array [].
Only include predictions with confidence_in_extraction >= 0.7

JSON Response:"""


async def extract_predictions_from_article(
    title: str,
    url: str,
    summary: str,
    source: str,
    published: str
) -> List[ExtractedPrediction]:
    """
    Use Claude to extract predictions from an article.
    """
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set")
        return []
    
    # For now, use the summary as content (full article fetching can be added later)
    content = summary
    
    prompt = EXTRACTION_PROMPT.format(
        title=title,
        source=source,
        published=published,
        content=content
    )
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                ANTHROPIC_API_URL,
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-haiku-20240307",  # Fast and cheap for extraction
                    "max_tokens": 2000,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
                return []
            
            result = response.json()
            content_text = result["content"][0]["text"]
            
            # Parse JSON response
            # Find JSON array in response
            start_idx = content_text.find('[')
            end_idx = content_text.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.info(f"No predictions found in: {title}")
                return []
            
            json_str = content_text[start_idx:end_idx]
            predictions_data = json.loads(json_str)
            
            predictions = []
            for p in predictions_data:
                if p.get("confidence_in_extraction", 0) >= 0.7:
                    predictions.append(ExtractedPrediction(
                        pundit_name=p.get("pundit_name", ""),
                        pundit_username=p.get("pundit_username"),
                        claim=p.get("claim", ""),
                        quote=p.get("quote", ""),
                        timeframe_description=p.get("timeframe_description", ""),
                        timeframe_days=p.get("timeframe_days", 365),
                        category=p.get("category", "general"),
                        specificity=p.get("specificity", 3),
                        verifiability=p.get("verifiability", 3),
                        boldness=p.get("boldness", 2),
                        stakes=p.get("stakes", 2),
                        confidence_in_extraction=p.get("confidence_in_extraction", 0.7)
                    ))
            
            logger.info(f"Extracted {len(predictions)} predictions from: {title}")
            return predictions
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Claude response: {e}")
        return []
    except Exception as e:
        logger.error(f"Error extracting predictions: {e}")
        return []


async def process_rss_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a batch of RSS articles and extract predictions.
    Returns list of extracted predictions with source info.
    """
    all_extractions = []
    
    for article in articles:
        predictions = await extract_predictions_from_article(
            title=article.get("title", ""),
            url=article.get("url", ""),
            summary=article.get("summary", ""),
            source=article.get("source", ""),
            published=article.get("published", "")
        )
        
        for pred in predictions:
            all_extractions.append({
                "source_url": article.get("url"),
                "source_title": article.get("title"),
                "source_published": article.get("published"),
                "prediction": {
                    "pundit_name": pred.pundit_name,
                    "pundit_username": pred.pundit_username,
                    "claim": pred.claim,
                    "quote": pred.quote,
                    "timeframe_description": pred.timeframe_description,
                    "timeframe_days": pred.timeframe_days,
                    "category": pred.category,
                    "tr_scores": {
                        "specificity": pred.specificity,
                        "verifiability": pred.verifiability,
                        "boldness": pred.boldness,
                        "stakes": pred.stakes
                    },
                    "confidence": pred.confidence_in_extraction
                }
            })
    
    return all_extractions
