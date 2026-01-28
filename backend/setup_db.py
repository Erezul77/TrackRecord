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

async def migrate_add_chain_columns():
    """Add hash chain columns to predictions table if they don't exist"""
    print("Checking for hash chain columns...")
    async with engine.begin() as conn:
        # Check if chain_hash column exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'predictions' AND column_name = 'chain_hash'
        """))
        
        if not result.fetchone():
            print("Adding chain_hash column...")
            await conn.execute(text("""
                ALTER TABLE predictions 
                ADD COLUMN chain_hash VARCHAR(64) UNIQUE
            """))
            
        # Check if chain_index column exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'predictions' AND column_name = 'chain_index'
        """))
        
        if not result.fetchone():
            print("Adding chain_index column...")
            await conn.execute(text("""
                ALTER TABLE predictions 
                ADD COLUMN chain_index INTEGER
            """))
            
        # Check if prev_chain_hash column exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'predictions' AND column_name = 'prev_chain_hash'
        """))
        
        if not result.fetchone():
            print("Adding prev_chain_hash column...")
            await conn.execute(text("""
                ALTER TABLE predictions 
                ADD COLUMN prev_chain_hash VARCHAR(64)
            """))
            
    print("Hash chain migration complete!")

async def migrate_add_horizon_column():
    """Add horizon column to predictions table if it doesn't exist"""
    print("Checking for horizon column...")
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'predictions' AND column_name = 'horizon'
        """))
        
        if not result.fetchone():
            print("Adding horizon column...")
            await conn.execute(text("""
                ALTER TABLE predictions 
                ADD COLUMN horizon VARCHAR(10)
            """))
            print("Horizon column added!")
        else:
            print("Horizon column already exists")
            
    print("Horizon migration complete!")

async def migrate_add_outcome_columns():
    """Add outcome, resolved_at, resolution_source columns to predictions table"""
    print("Checking for outcome columns...")
    async with engine.begin() as conn:
        # Check and add outcome column
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'predictions' AND column_name = 'outcome'
        """))
        
        if not result.fetchone():
            print("Adding outcome column...")
            await conn.execute(text("""
                ALTER TABLE predictions 
                ADD COLUMN outcome VARCHAR(10)
            """))
            print("Outcome column added!")
        else:
            print("Outcome column already exists")
        
        # Check and add resolved_at column
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'predictions' AND column_name = 'resolved_at'
        """))
        
        if not result.fetchone():
            print("Adding resolved_at column...")
            await conn.execute(text("""
                ALTER TABLE predictions 
                ADD COLUMN resolved_at TIMESTAMP
            """))
            print("resolved_at column added!")
        else:
            print("resolved_at column already exists")
        
        # Check and add resolution_source column
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'predictions' AND column_name = 'resolution_source'
        """))
        
        if not result.fetchone():
            print("Adding resolution_source column...")
            await conn.execute(text("""
                ALTER TABLE predictions 
                ADD COLUMN resolution_source VARCHAR(50)
            """))
            print("resolution_source column added!")
        else:
            print("resolution_source column already exists")
            
    print("Outcome migration complete!")

async def full_setup():
    """Run full setup including migrations"""
    try:
        await setup_db()
    except Exception as e:
        print(f"Warning: setup_db failed: {e}")
    
    try:
        await migrate_add_chain_columns()
    except Exception as e:
        print(f"Warning: chain migration failed: {e}")
    
    try:
        await migrate_add_horizon_column()
    except Exception as e:
        print(f"Warning: horizon migration failed: {e}")
    
    try:
        await migrate_add_outcome_columns()
    except Exception as e:
        print(f"Warning: outcome migration failed: {e}")
    
    print("Setup complete (with possible warnings above)")

if __name__ == "__main__":
    asyncio.run(full_setup())
