import asyncio
from database.session import engine
from database.models import Base
from sqlalchemy import text

async def setup_db():
    print("Connecting to database...")
    async with engine.begin() as conn:
        # Enable pgvector extension
        print("Enabling pgvector extension...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        
        # Create all tables
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        
    print("Database setup complete!")

if __name__ == "__main__":
    asyncio.run(setup_db())
