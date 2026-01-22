# services/polymarket.py
"""
Polymarket API Integration
Fetches markets, searches for matches, and retrieves prices
"""
import httpx
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio

# Polymarket API endpoints
POLYMARKET_API = "https://clob.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"


@dataclass
class PolymarketMarket:
    id: str
    question: str
    description: str
    slug: str
    end_date: Optional[datetime]
    outcome_prices: Dict[str, float]  # {"Yes": 0.65, "No": 0.35}
    volume: float
    liquidity: float
    active: bool
    category: str


class PolymarketService:
    """Service for interacting with Polymarket API"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search_markets(self, query: str, limit: int = 10) -> List[PolymarketMarket]:
        """Search for markets matching a query"""
        try:
            # Use Gamma API for searching
            response = await self.client.get(
                f"{GAMMA_API}/markets",
                params={
                    "search": query,
                    "limit": limit,
                    "active": "true"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            markets = []
            for item in data:
                market = self._parse_market(item)
                if market:
                    markets.append(market)
            
            return markets
            
        except Exception as e:
            print(f"Error searching Polymarket: {e}")
            return []
    
    async def get_market_by_id(self, market_id: str) -> Optional[PolymarketMarket]:
        """Get a specific market by ID"""
        try:
            response = await self.client.get(f"{GAMMA_API}/markets/{market_id}")
            response.raise_for_status()
            data = response.json()
            return self._parse_market(data)
        except Exception as e:
            print(f"Error fetching market {market_id}: {e}")
            return None
    
    async def get_active_markets(self, category: Optional[str] = None, limit: int = 50) -> List[PolymarketMarket]:
        """Get active markets, optionally filtered by category"""
        try:
            params = {"active": "true", "limit": limit}
            if category:
                params["tag"] = category
                
            response = await self.client.get(f"{GAMMA_API}/markets", params=params)
            response.raise_for_status()
            data = response.json()
            
            markets = []
            for item in data:
                market = self._parse_market(item)
                if market:
                    markets.append(market)
            
            return markets
            
        except Exception as e:
            print(f"Error fetching active markets: {e}")
            return []
    
    async def get_market_price(self, condition_id: str) -> Optional[float]:
        """Get current price for a market condition"""
        try:
            response = await self.client.get(
                f"{CLOB_API}/price",
                params={"token_id": condition_id}
            )
            response.raise_for_status()
            data = response.json()
            return float(data.get("price", 0))
        except Exception as e:
            print(f"Error fetching price: {e}")
            return None
    
    def _parse_market(self, data: dict) -> Optional[PolymarketMarket]:
        """Parse raw API response into PolymarketMarket"""
        try:
            # Extract outcome prices
            outcome_prices = {}
            if "outcomePrices" in data:
                prices = data["outcomePrices"]
                if isinstance(prices, list) and len(prices) >= 2:
                    outcome_prices = {"Yes": float(prices[0]), "No": float(prices[1])}
            elif "tokens" in data:
                for token in data.get("tokens", []):
                    outcome_prices[token.get("outcome", "Unknown")] = float(token.get("price", 0))
            
            # Parse end date
            end_date = None
            if data.get("endDate"):
                try:
                    end_date = datetime.fromisoformat(data["endDate"].replace("Z", "+00:00"))
                except:
                    pass
            
            return PolymarketMarket(
                id=data.get("id") or data.get("conditionId", ""),
                question=data.get("question", ""),
                description=data.get("description", ""),
                slug=data.get("slug", ""),
                end_date=end_date,
                outcome_prices=outcome_prices,
                volume=float(data.get("volume", 0) or 0),
                liquidity=float(data.get("liquidity", 0) or 0),
                active=data.get("active", True),
                category=data.get("category", data.get("tag", "general"))
            )
        except Exception as e:
            print(f"Error parsing market: {e}")
            return None
    
    async def close(self):
        await self.client.aclose()


class MarketMatcher:
    """Match predictions to Polymarket markets using semantic similarity"""
    
    def __init__(self):
        self.polymarket = PolymarketService()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
    
    async def find_matching_markets(
        self, 
        prediction_claim: str,
        prediction_category: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find Polymarket markets that match a prediction claim
        Returns list of potential matches with similarity scores
        """
        # Extract key terms for search
        search_terms = self._extract_search_terms(prediction_claim)
        
        # Search Polymarket
        all_markets = []
        for term in search_terms[:3]:  # Limit searches
            markets = await self.polymarket.search_markets(term, limit=10)
            all_markets.extend(markets)
        
        # Remove duplicates
        seen_ids = set()
        unique_markets = []
        for m in all_markets:
            if m.id not in seen_ids:
                seen_ids.add(m.id)
                unique_markets.append(m)
        
        if not unique_markets:
            return []
        
        # Score matches using simple keyword similarity
        # (In production, use OpenAI embeddings for semantic similarity)
        scored_matches = []
        for market in unique_markets:
            score = self._calculate_similarity(prediction_claim, market.question)
            if score > 0.1:  # Minimum threshold
                scored_matches.append({
                    "market_id": market.id,
                    "market_question": market.question,
                    "market_slug": market.slug,
                    "market_end_date": market.end_date.isoformat() if market.end_date else None,
                    "current_yes_price": market.outcome_prices.get("Yes", 0.5),
                    "current_no_price": market.outcome_prices.get("No", 0.5),
                    "volume": market.volume,
                    "similarity_score": score,
                    "match_confidence": "high" if score > 0.6 else "medium" if score > 0.3 else "low"
                })
        
        # Sort by similarity score
        scored_matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return scored_matches[:top_k]
    
    def _extract_search_terms(self, claim: str) -> List[str]:
        """Extract key search terms from a prediction claim"""
        # Remove common words and extract key phrases
        stop_words = {
            'will', 'be', 'the', 'a', 'an', 'to', 'of', 'in', 'for', 'on', 'at',
            'by', 'with', 'that', 'this', 'is', 'are', 'was', 'were', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'would', 'could', 'should',
            'may', 'might', 'can', 'and', 'or', 'but', 'not', 'no', 'yes'
        }
        
        words = claim.lower().split()
        key_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Build search terms
        terms = []
        
        # Full claim (truncated)
        terms.append(claim[:100])
        
        # Key phrases (consecutive important words)
        if len(key_words) >= 2:
            terms.append(' '.join(key_words[:4]))
        
        # Individual important terms
        for word in key_words[:3]:
            if len(word) > 4:
                terms.append(word)
        
        return terms
    
    def _calculate_similarity(self, claim: str, market_question: str) -> float:
        """
        Calculate text similarity between prediction and market question
        Simple word overlap - in production use embeddings
        """
        claim_words = set(claim.lower().split())
        market_words = set(market_question.lower().split())
        
        # Remove very common words
        common = {'will', 'be', 'the', 'a', 'an', 'to', 'of', 'in', 'for', 'on', '?'}
        claim_words -= common
        market_words -= common
        
        if not claim_words or not market_words:
            return 0.0
        
        # Jaccard similarity
        intersection = len(claim_words & market_words)
        union = len(claim_words | market_words)
        
        return intersection / union if union > 0 else 0.0
    
    async def close(self):
        await self.polymarket.close()


# Standalone test
async def test_polymarket():
    service = PolymarketService()
    
    print("Searching for Bitcoin markets...")
    markets = await service.search_markets("Bitcoin price", limit=5)
    
    for market in markets:
        print(f"\n📊 {market.question}")
        print(f"   Yes: {market.outcome_prices.get('Yes', 'N/A'):.2%}")
        print(f"   Volume: ${market.volume:,.0f}")
        print(f"   Slug: {market.slug}")
    
    await service.close()
    
    print("\n\nTesting MarketMatcher...")
    matcher = MarketMatcher()
    
    test_claim = "Bitcoin will reach $100,000 by end of 2026"
    matches = await matcher.find_matching_markets(test_claim, "crypto")
    
    print(f"\nMatches for: '{test_claim}'")
    for match in matches:
        print(f"\n  ✓ {match['market_question']}")
        print(f"    Similarity: {match['similarity_score']:.2f}")
        print(f"    Yes Price: {match['current_yes_price']:.2%}")
    
    await matcher.close()


if __name__ == "__main__":
    asyncio.run(test_polymarket())
