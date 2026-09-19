import os
import asyncio
import pytest

# Explicitly isolate test environment configuration from production configuration
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_hireflow.db"
os.environ["USE_SQLITE_LOCAL_FALLBACK"] = "true"

from app.core.config import settings
from app.core.db import init_db, engine
from app.models.base import Base


@pytest.fixture(autouse=True, scope="function")
def setup_test_database():
    """Ensure clean test database tables and initial seed data are populated for every test."""
    async def _reset():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await init_db()

    asyncio.run(_reset())
    yield


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_database():
    """Session teardown removing test SQLite file."""
    yield
    # Remove test SQLite database if exists
    test_db_path = "./test_hireflow.db"
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except Exception:
            pass
