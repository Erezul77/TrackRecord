import os
import asyncio
import logging
from datetime import datetime
from typing import List
import tweepy
from database.models import RawContent, Pundit
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib

logger = logging.getLogger(__name__)

class TwitterSource:
    def __init__(self, bearer_token: str):
        self.client = tweepy.Client(bearer_token=bearer_token)

    async def fetch_new_content(self, pundit: Pundit) -> List[dict]:
        """
        Fetch recent tweets from a pundit
        """
        if not pundit.twitter_id:
            return []

        try:
            # Note: tweepy.Client is sync, in a real app you might use an async wrapper or run in executor
            tweets = self.client.get_users_tweets(
                id=pundit.twitter_id,
                max_results=10,
                since_id=pundit.last_tweet_id,
                tweet_fields=['created_at', 'conversation_id']
            )
            
            if not tweets.data:
                return []

            results = []
            for tweet in tweets.data:
                results.append({
                    'text': tweet.text,
                    'url': f"https://twitter.com/x/status/{tweet.id}",
                    'published_at': tweet.created_at,
                    'source_type': 'twitter',
                    'metadata': {
                        'tweet_id': tweet.id,
                        'conversation_id': tweet.conversation_id
                    }
                })
            
            # Update last_tweet_id (should be saved to DB by orchestrator)
            pundit.last_tweet_id = str(tweets.data[0].id)
            
            return results
        except Exception as e:
            logger.error(f"Failed to fetch tweets for {pundit.name}: {e}")
            return []

class IngestionPipeline:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.sources = {
            'twitter': TwitterSource(bearer_token=os.getenv('TWITTER_BEARER_TOKEN', ''))
        }

    async def run_sync(self):
        """
        One-time sync for all tracked pundits
        """
        # Get all tracked pundits
        result = await self.db.execute(select(Pundit))
        pundits = result.scalars().all()

        for pundit in pundits:
            for source_name, source in self.sources.items():
                new_items = await source.fetch_new_content(pundit)
                
                for item in new_items:
                    # Deduplicate with hash
                    content_hash = hashlib.sha256(f"{item['text']}|{item['published_at']}".encode()).hexdigest()
                    
                    # Check if already exists
                    existing = await self.db.execute(
                        select(RawContent).where(RawContent.content_hash == content_hash)
                    )
                    if existing.scalar_one_or_none():
                        continue

                    raw_content = RawContent(
                        pundit_id=pundit.id,
                        source_type=item['source_type'],
                        text=item['text'],
                        url=item['url'],
                        published_at=item['published_at'],
                        metadata_json=item['metadata'],
                        content_hash=content_hash
                    )
                    self.db.add(raw_content)
                
                pundit.last_checked_at = datetime.utcnow()
        
        await self.db.commit()
