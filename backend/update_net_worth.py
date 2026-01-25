# update_net_worth.py
"""
Script to update net worth data for existing pundits in the database.
Run this after adding the net_worth columns to the database.
"""
import asyncio
from sqlalchemy import select, text
from database.session import async_session
from database.models import Pundit

# Net worth data for pundits (in USD millions)
# Source: Forbes, Bloomberg, Celebrity Net Worth estimates as of 2024-2025
NET_WORTH_DATA = {
    # Finance / Markets
    "balajis": {"net_worth": 500, "source": "Forbes estimate", "year": 2024},
    "jimcramer": {"net_worth": 150, "source": "Celebrity Net Worth", "year": 2024},
    "CathieDWood": {"net_worth": 250, "source": "Forbes", "year": 2024},
    "PeterSchiff": {"net_worth": 100, "source": "Celebrity Net Worth", "year": 2024},
    "saylor": {"net_worth": 4000, "source": "Forbes", "year": 2025},
    "elonmusk": {"net_worth": 330000, "source": "Forbes Real-Time", "year": 2025},
    "tomleefundstrat": {"net_worth": 50, "source": "Estimate", "year": 2024},
    "theRealKiyosaki": {"net_worth": 100, "source": "Celebrity Net Worth", "year": 2024},
    "BillAckman": {"net_worth": 9000, "source": "Forbes", "year": 2024},
    "raydalio": {"net_worth": 15300, "source": "Forbes", "year": 2024},
    "Nouriel": {"net_worth": 25, "source": "Estimate", "year": 2024},
    "TimDraper": {"net_worth": 2000, "source": "Forbes", "year": 2024},
    
    # Economists
    "paulkrugman": {"net_worth": 5, "source": "Estimate", "year": 2024},
    "LHSummers": {"net_worth": 40, "source": "Estimate", "year": 2024},
    
    # Politics - US
    "realDonaldTrump": {"net_worth": 6500, "source": "Forbes", "year": 2025},
    "JoeBiden": {"net_worth": 10, "source": "Forbes", "year": 2024},
    "AOC": {"net_worth": 0.5, "source": "Celebrity Net Worth", "year": 2024},
    "NateSilver538": {"net_worth": 5, "source": "Estimate", "year": 2024},
    
    # International Politicians
    "BorisJohnson": {"net_worth": 4, "source": "Celebrity Net Worth", "year": 2024},
    "NigelFarage": {"net_worth": 3, "source": "Estimate", "year": 2024},
    "EmmanuelMacron": {"net_worth": 5, "source": "Estimate", "year": 2024},
    "naaborrmodi": {"net_worth": 0.5, "source": "Official Declaration", "year": 2024},
    "JMilei": {"net_worth": 1, "source": "Estimate", "year": 2024},
    "LulaOficial": {"net_worth": 1.5, "source": "Estimate", "year": 2024},
    "ZelenskyyUa": {"net_worth": 20, "source": "Estimate", "year": 2023},
    "RTErdogan": {"net_worth": 50, "source": "Estimate", "year": 2024},
    
    # Sports Commentators
    "stephenasmith": {"net_worth": 16, "source": "Celebrity Net Worth", "year": 2024},
    "RealSkipBayless": {"net_worth": 17, "source": "Celebrity Net Worth", "year": 2024},
    "GNev2": {"net_worth": 70, "source": "Celebrity Net Worth", "year": 2024},
    "GaryLineker": {"net_worth": 40, "source": "Celebrity Net Worth", "year": 2024},
    "FabrizioRomano": {"net_worth": 5, "source": "Estimate", "year": 2024},
    
    # Science / Health
    "NIAIDNews": {"net_worth": 12, "source": "Estimate", "year": 2024},  # Fauci
    "neiltyson": {"net_worth": 5, "source": "Celebrity Net Worth", "year": 2024},
    
    # Historic Finance Figures
    "benbernanke": {"net_worth": 3, "source": "Estimate", "year": 2024},
    
    # Tech
    "sama": {"net_worth": 1000, "source": "Bloomberg", "year": 2024},  # Sam Altman
}


async def add_columns_if_not_exist():
    """Add net_worth columns to pundits table if they don't exist"""
    async with async_session() as session:
        try:
            await session.execute(text("""
                ALTER TABLE pundits 
                ADD COLUMN IF NOT EXISTS net_worth FLOAT,
                ADD COLUMN IF NOT EXISTS net_worth_source VARCHAR(100),
                ADD COLUMN IF NOT EXISTS net_worth_year INTEGER
            """))
            await session.commit()
            print("Columns added/verified successfully!")
        except Exception as e:
            print(f"Note: {e}")


async def update_net_worth():
    """Update net worth for existing pundits"""
    await add_columns_if_not_exist()
    
    async with async_session() as session:
        # Get all pundits
        result = await session.execute(select(Pundit))
        pundits = result.scalars().all()
        
        updated = 0
        for pundit in pundits:
            username = pundit.username
            if username in NET_WORTH_DATA:
                data = NET_WORTH_DATA[username]
                pundit.net_worth = data["net_worth"]
                pundit.net_worth_source = data["source"]
                pundit.net_worth_year = data["year"]
                updated += 1
                print(f"Updated {pundit.name}: ${data['net_worth']}M ({data['source']})")
        
        await session.commit()
        print(f"\nUpdated {updated} pundits with net worth data!")


if __name__ == "__main__":
    asyncio.run(update_net_worth())
