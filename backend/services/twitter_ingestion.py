# services/twitter_ingestion.py
"""
Twitter/X API Integration
Fetches tweets from tracked pundits and extracts predictions
"""
import os
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Twitter API v2 endpoints
TWITTER_API_BASE = "https://api.twitter.com/2"


@dataclass
class Tweet:
    id: str
    text: str
    author_id: str
    author_username: str
    author_name: str
    created_at: datetime
    url: str
    metrics: Dict[str, int]  # likes, retweets, replies


class TwitterService:
    """Service for fetching tweets from Twitter/X API v2"""
    
    def __init__(self, bearer_token: Optional[str] = None):
        self.bearer_token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN")
        if not self.bearer_token:
            raise ValueError("Twitter Bearer Token not configured")
        
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(timeout=30.0, headers=self.headers)
    
    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user info by username"""
        try:
            # Remove @ if present
            username = username.lstrip("@")
            
            response = await self.client.get(
                f"{TWITTER_API_BASE}/users/by/username/{username}",
                params={
                    "user.fields": "id,name,username,description,public_metrics,verified"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data")
            else:
                logger.warning(f"Failed to get user {username}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching user {username}: {e}")
            return None
    
    async def get_user_tweets(
        self, 
        user_id: str,
        max_results: int = 10,
        since_id: Optional[str] = None,
        start_time: Optional[datetime] = None
    ) -> List[Tweet]:
        """Fetch recent tweets from a user"""
        try:
            params = {
                "max_results": min(max_results, 100),  # API limit
                "tweet.fields": "id,text,created_at,public_metrics,author_id",
                "expansions": "author_id",
                "user.fields": "id,name,username"
            }
            
            if since_id:
                params["since_id"] = since_id
            
            if start_time:
                params["start_time"] = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            response = await self.client.get(
                f"{TWITTER_API_BASE}/users/{user_id}/tweets",
                params=params
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to get tweets for user {user_id}: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            tweets_data = data.get("data", [])
            
            # Get user info from includes
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
            
            tweets = []
            for tweet_data in tweets_data:
                author = users.get(tweet_data["author_id"], {})
                
                tweet = Tweet(
                    id=tweet_data["id"],
                    text=tweet_data["text"],
                    author_id=tweet_data["author_id"],
                    author_username=author.get("username", "unknown"),
                    author_name=author.get("name", "Unknown"),
                    created_at=datetime.fromisoformat(tweet_data["created_at"].replace("Z", "+00:00")),
                    url=f"https://twitter.com/{author.get('username', 'i')}/status/{tweet_data['id']}",
                    metrics=tweet_data.get("public_metrics", {})
                )
                tweets.append(tweet)
            
            return tweets
            
        except Exception as e:
            logger.error(f"Error fetching tweets for user {user_id}: {e}")
            return []
    
    async def search_tweets(
        self,
        query: str,
        max_results: int = 10,
        start_time: Optional[datetime] = None
    ) -> List[Tweet]:
        """Search for tweets matching a query"""
        try:
            params = {
                "query": query,
                "max_results": min(max_results, 100),
                "tweet.fields": "id,text,created_at,public_metrics,author_id",
                "expansions": "author_id",
                "user.fields": "id,name,username"
            }
            
            if start_time:
                params["start_time"] = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            response = await self.client.get(
                f"{TWITTER_API_BASE}/tweets/search/recent",
                params=params
            )
            
            if response.status_code != 200:
                logger.warning(f"Search failed: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            tweets_data = data.get("data", [])
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
            
            tweets = []
            for tweet_data in tweets_data:
                author = users.get(tweet_data["author_id"], {})
                
                tweet = Tweet(
                    id=tweet_data["id"],
                    text=tweet_data["text"],
                    author_id=tweet_data["author_id"],
                    author_username=author.get("username", "unknown"),
                    author_name=author.get("name", "Unknown"),
                    created_at=datetime.fromisoformat(tweet_data["created_at"].replace("Z", "+00:00")),
                    url=f"https://twitter.com/{author.get('username', 'i')}/status/{tweet_data['id']}",
                    metrics=tweet_data.get("public_metrics", {})
                )
                tweets.append(tweet)
            
            return tweets
            
        except Exception as e:
            logger.error(f"Error searching tweets: {e}")
            return []
    
    async def close(self):
        await self.client.aclose()


class TwitterPredictionCollector:
    """Collects predictions from tracked pundits on Twitter"""
    
    # Prediction-related keywords to filter tweets
    PREDICTION_KEYWORDS = [
        "predict", "prediction", "forecast", "will be", "going to",
        "by 2025", "by 2026", "by 2027", "by end of", "by the end",
        "mark my words", "calling it now", "bet", "i believe",
        "will reach", "will hit", "will win", "will lose",
        "expect", "expecting", "my prediction", "hot take"
    ]
    
    def __init__(self, bearer_token: Optional[str] = None):
        self.twitter = TwitterService(bearer_token)
    
    def is_prediction_tweet(self, text: str) -> bool:
        """Check if a tweet likely contains a prediction"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.PREDICTION_KEYWORDS)
    
    async def collect_from_pundit(
        self,
        username: str,
        since_hours: int = 24
    ) -> List[Tweet]:
        """Collect prediction tweets from a specific pundit"""
        # Get user ID
        user = await self.twitter.get_user_by_username(username)
        if not user:
            logger.warning(f"Could not find user: {username}")
            return []
        
        user_id = user["id"]
        
        # Fetch recent tweets
        start_time = datetime.utcnow() - timedelta(hours=since_hours)
        tweets = await self.twitter.get_user_tweets(
            user_id=user_id,
            max_results=20,
            start_time=start_time
        )
        
        # Filter for prediction tweets
        prediction_tweets = [t for t in tweets if self.is_prediction_tweet(t.text)]
        
        logger.info(f"Found {len(prediction_tweets)} prediction tweets from @{username}")
        return prediction_tweets
    
    async def collect_from_multiple_pundits(
        self,
        usernames: List[str],
        since_hours: int = 24
    ) -> Dict[str, List[Tweet]]:
        """Collect predictions from multiple pundits"""
        results = {}
        
        for username in usernames:
            try:
                tweets = await self.collect_from_pundit(username, since_hours)
                results[username] = tweets
                
                # Rate limiting - be nice to the API
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error collecting from {username}: {e}")
                results[username] = []
        
        return results
    
    async def search_prediction_tweets(
        self,
        pundit_usernames: List[str],
        additional_keywords: Optional[List[str]] = None
    ) -> List[Tweet]:
        """Search for prediction tweets from specific users"""
        # Build search query
        # Format: (from:user1 OR from:user2) (predict OR forecast OR "will be")
        
        if len(pundit_usernames) > 10:
            pundit_usernames = pundit_usernames[:10]  # API limitation
        
        from_clause = " OR ".join([f"from:{u.lstrip('@')}" for u in pundit_usernames])
        
        keywords = additional_keywords or ["predict", "forecast", "will be", "by 2025"]
        keyword_clause = " OR ".join(keywords[:5])
        
        query = f"({from_clause}) ({keyword_clause}) -is:retweet"
        
        start_time = datetime.utcnow() - timedelta(days=7)  # Last 7 days
        
        return await self.twitter.search_tweets(
            query=query,
            max_results=50,
            start_time=start_time
        )
    
    async def close(self):
        await self.twitter.close()


# Helper function to get tracked pundits with Twitter handles
def get_twitter_pundits() -> List[str]:
    """Get list of Twitter usernames for tracked pundits"""
    from services.rss_ingestion import KNOWN_PUNDITS
    return list(KNOWN_PUNDITS.keys())


async def test_twitter():
    """Test Twitter API connection"""
    print("Testing Twitter API...")
    
    try:
        collector = TwitterPredictionCollector()
        
        # Test getting a user
        print("\nFetching user @elonmusk...")
        user = await collector.twitter.get_user_by_username("elonmusk")
        if user:
            print(f"Found: {user['name']} (@{user['username']})")
            print(f"Followers: {user.get('public_metrics', {}).get('followers_count', 'N/A')}")
        
        # Test fetching tweets
        print("\nFetching recent tweets...")
        tweets = await collector.collect_from_pundit("elonmusk", since_hours=168)
        
        print(f"\nFound {len(tweets)} potential prediction tweets:")
        for tweet in tweets[:3]:
            print(f"\n- {tweet.text[:200]}...")
            print(f"  URL: {tweet.url}")
            print(f"  Likes: {tweet.metrics.get('like_count', 0)}")
        
        await collector.close()
        print("\n✅ Twitter API working!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_twitter())
