import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.base import Base
from app.models.organization import Organization
from app.models.user import User

logger = logging.getLogger("hireflow.db")

# Configure async engine
is_sqlite = "sqlite" in settings.async_database_url
connect_args = {"check_same_thread": False} if is_sqlite else {}

if is_sqlite:
    logger.warning(
        "[DB CONFIG] Explicit local/test SQLite fallback active: %s. "
        "Production runtime requires PostgreSQL 15+ with pgvector.",
        settings.async_database_url,
    )
else:
    logger.info(
        "[DB CONFIG] Connecting to authoritative PostgreSQL engine: %s",
        settings.async_database_url.split("@")[-1] if "@" in settings.async_database_url else "configured",
    )

engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True if not is_sqlite else False,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an active database session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables and seed default demo data if not present."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed demo organization and personas if empty
    async with async_session_factory() as session:
        result = await session.execute(select(Organization).limit(1))
        existing_org = result.scalar_one_or_none()

        if not existing_org:
            demo_org = Organization(
                name="Acme Technologies",
                slug="acme-tech",
            )
            session.add(demo_org)
            await session.flush()

            # Seed Demo Recruiter: Sarah Jenkins
            sarah = User(
                org_id=demo_org.id,
                email="sarah.jenkins@hireflow.demo",
                full_name="Sarah Jenkins",
                role="recruiter",
                preferences={
                    "department": "Engineering",
                    "evaluation_priority": "technical_depth",
                    "persona_id": "sarah_jenkins",
                },
            )

            # Seed Demo Hiring Manager: Marcus Vance
            marcus = User(
                org_id=demo_org.id,
                email="marcus.vance@hireflow.demo",
                full_name="Marcus Vance",
                role="hiring_manager",
                preferences={
                    "department": "Engineering Leadership",
                    "evaluation_priority": "leadership_and_problem_solving",
                    "persona_id": "marcus_vance",
                },
            )

            session.add_all([sarah, marcus])
            await session.commit()
