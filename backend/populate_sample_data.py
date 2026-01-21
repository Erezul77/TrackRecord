# populate_sample_data.py
import asyncio
import uuid
from datetime import datetime, timedelta
from database.session import async_session
from database.models import Pundit, PunditMetrics, Prediction, RawContent, Match, Position
from sqlalchemy import text
import hashlib

async def populate():
    print("Starting sample data population...")
    async with async_session() as session:
        # Create some pundits
        pundits_data = [
            {
                "name": "Nate Silver",
                "username": "NateSilver538",
                "affiliation": "Silver Bulletin",
                "bio": "Founder of FiveThirtyEight. Statistician and writer.",
                "domains": ["politics", "economy"],
                "pnl": 12500.50,
                "win_rate": 0.68,
                "roi": 0.15
            },
            {
                "name": "Balaji Srinivasan",
                "username": "balajis",
                "affiliation": "Independent",
                "bio": "Entrepreneur and investor. Former CTO of Coinbase.",
                "domains": ["crypto", "tech"],
                "pnl": -2100.20,
                "win_rate": 0.35,
                "roi": -0.08
            },
            {
                "name": "Jim Cramer",
                "username": "jimcramer",
                "affiliation": "CNBC",
                "bio": "Host of Mad Money. Former hedge fund manager.",
                "domains": ["markets", "economy"],
                "pnl": -5400.00,
                "win_rate": 0.42,
                "roi": -0.12
            }
        ]

        pundit_objects = []
        for p_data in pundits_data:
            p_id = uuid.uuid4()
            pundit = Pundit(
                id=p_id,
                name=p_data["name"],
                username=p_data["username"],
                affiliation=p_data["affiliation"],
                bio=p_data["bio"],
                domains=p_data["domains"],
                verified=True,
                verified_at=datetime.utcnow() - timedelta(days=30),
                avatar_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed={p_data['username']}"
            )
            session.add(pundit)
            
            metrics = PunditMetrics(
                pundit_id=p_id,
                total_predictions=15,
                matched_predictions=12,
                resolved_predictions=10,
                paper_total_pnl=p_data["pnl"],
                paper_win_rate=p_data["win_rate"],
                paper_roi=p_data["roi"],
                pnl_30d=p_data["pnl"] * 0.2
            )
            session.add(metrics)
            pundit_objects.append(pundit)

        await session.commit()
        print(f"Created {len(pundit_objects)} pundits.")

        # Create some predictions for Nate Silver
        nate_id = pundit_objects[0].id
        nate_predictions = [
            {
                "claim": "The Democratic candidate will win the 2024 Presidential Election",
                "quote": "If I had to bet my house right now, I'd say the blue wall holds.",
                "confidence": 0.65,
                "category": "politics",
                "status": "matched"
            },
            {
                "claim": "Inflation will drop below 3% by Q3 2024",
                "quote": "The structural trends suggest we've reached peak inflation and will see sub-3% numbers soon.",
                "confidence": 0.80,
                "category": "economy",
                "status": "pending_match"
            }
        ]

        for pred_data in nate_predictions:
            pred_id = uuid.uuid4()
            published_at = datetime.utcnow() - timedelta(days=5)
            content_hash = hashlib.sha256(f"{nate_id}|{pred_data['claim']}|{published_at.isoformat()}".encode()).hexdigest()
            
            prediction = Prediction(
                id=pred_id,
                pundit_id=nate_id,
                claim=pred_data["claim"],
                confidence=pred_data["confidence"],
                timeframe=datetime.utcnow() + timedelta(days=200),
                quote=pred_data["quote"],
                category=pred_data["category"],
                source_url="https://twitter.com/NateSilver538/status/123",
                source_type="twitter",
                captured_at=datetime.utcnow() - timedelta(days=1),
                content_hash=content_hash,
                status=pred_data["status"]
            )
            session.add(prediction)

            if pred_data["status"] == "matched":
                # Create a match
                match_id = uuid.uuid4()
                match = Match(
                    id=match_id,
                    prediction_id=pred_id,
                    market_id="polymarket-123",
                    market_slug="2024-election-winner",
                    market_question="Who will win the 2024 US Presidential Election?",
                    similarity_score=0.92,
                    match_type="auto_matched",
                    entry_price=0.52,
                    entry_timestamp=datetime.utcnow() - timedelta(days=1)
                )
                session.add(match)

                # Create a position
                pos_id = uuid.uuid4()
                pos = Position(
                    id=pos_id,
                    prediction_id=pred_id,
                    match_id=match_id,
                    pundit_id=nate_id,
                    market_id="polymarket-123",
                    market_question=match.market_question,
                    entry_price=0.52,
                    entry_timestamp=match.entry_timestamp,
                    position_size=500.0,
                    shares=500.0 / 0.52,
                    status='open',
                    current_price=0.55,
                    unrealized_pnl=(500.0 / 0.52) * 0.55 - 500.0
                )
                session.add(pos)

        await session.commit()
        print("Created sample predictions, matches, and positions.")

    print("Population complete!")

if __name__ == "__main__":
    asyncio.run(populate())
