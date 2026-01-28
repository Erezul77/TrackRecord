import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://trackrecord:trackrecord@localhost/trackrecord")

# Async engine for FastAPI endpoints with connection pooling
engine = create_async_engine(
    DATABASE_URL, 
    echo=False,  # Disable SQL logging in production for performance
    pool_size=10,  # Number of connections to keep in the pool
    max_overflow=20,  # Additional connections when pool is exhausted
    pool_timeout=30,  # Seconds to wait for a connection
    pool_recycle=1800,  # Recycle connections after 30 minutes
    pool_pre_ping=True,  # Check connection health before using
)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Sync engine for background jobs (auto-agent)
# Convert asyncpg URL to psycopg2 format and fix SSL parameter
SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")
SYNC_DATABASE_URL = SYNC_DATABASE_URL.replace("ssl=require", "sslmode=require")
if not SYNC_DATABASE_URL.startswith("postgresql+psycopg2://"):
    SYNC_DATABASE_URL = SYNC_DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")

sync_engine = create_engine(
    SYNC_DATABASE_URL, 
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)

async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_sync_db():
    """Get a synchronous database session for background jobs"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
