"""
Demo Seed CLI Script (Phase 7).
Can be run from command line: python -m scripts.seed_demo_data or python scripts/seed_demo_data.py
Populates the database with realistic demo jobs, candidates, matches, interviews, evaluations, and audit logs.
"""
import asyncio
import logging
import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.db import async_session_factory, init_db
from app.models.organization import Organization
from app.models.user import User
from app.routers.demo import seed_demo_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_demo_data")


async def main():
    logger.info("Initializing database schema if needed...")
    await init_db()

    async with async_session_factory() as session:
        # Fetch the default recruiter Sarah Jenkins
        result = await session.execute(
            select(User).where(User.email == "sarah.jenkins@hireflow.demo").limit(1)
        )
        user = result.scalar_one_or_none()
        if not user:
            # Fallback: any user
            result = await session.execute(select(User).limit(1))
            user = result.scalar_one_or_none()

        if not user:
            logger.error("No user found in database. Run init_db first.")
            return

        logger.info(f"Seeding demo data for user: {user.email} (Org ID: {user.org_id})...")
        res = await seed_demo_data(current_user=user, db=session)
        logger.info(f"Demo seeding result: {res}")


if __name__ == "__main__":
    asyncio.run(main())
