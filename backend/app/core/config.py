import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,https://hire-flow-nu-blush.vercel.app"
    SECRET_KEY: str = "hireflow-hackathon-insecure-dev-secret-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # =====================================================================
    # Authoritative Database Configuration (PostgreSQL 15+ with pgvector)
    # =====================================================================
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/hireflow"
    PGVECTOR_DISTANCE_STRATEGY: str = "cosine"

    # Explicit local test / dev fallback configuration (NEVER silent in production)
    USE_SQLITE_LOCAL_FALLBACK: bool = False
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///./test_hireflow.db"

    # AI / LLM
    OPENAI_API_KEY: str = "sk-mock-key-for-development"
    OPENAI_MODEL_FAST: str = "gpt-4o-mini"
    OPENAI_MODEL_REASONING: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # Observability
    ENABLE_AUDIT_LOGGING: bool = True
    COST_PER_1K_PROMPT_TOKENS: float = 0.00015
    COST_PER_1K_COMPLETION_TOKENS: float = 0.00060

    model_config = {
        "env_file": [".env", "../.env"],
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def cors_origins_list(self) -> List[str]:
        raw = self.CORS_ORIGINS
        if not raw:
            return []
        origins = []
        for origin in raw.split(","):
            cleaned = origin.strip().strip("\"'").rstrip("/")
            if cleaned:
                origins.append(cleaned)
        return origins

    @property
    def async_database_url(self) -> str:
        """
        Derive the async database URL.
        Converts postgresql:// to postgresql+asyncpg:// for SQLAlchemy 2.0 async engine.
        If USE_SQLITE_LOCAL_FALLBACK is explicitly enabled and DATABASE_URL is not set to Postgres,
        routes to isolated local SQLite fallback.
        """
        if self.USE_SQLITE_LOCAL_FALLBACK:
            if "sqlite" in self.DATABASE_URL.lower():
                url = self.DATABASE_URL
                if url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
                    return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
                return url
            return self.TEST_DATABASE_URL

        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        if url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
            return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return url


settings = Settings()
