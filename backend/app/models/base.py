from datetime import datetime, timezone
import json
from typing import List, Optional
from sqlalchemy import DateTime, JSON
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VectorEmbedding(TypeDecorator):
    """
    Dual-compatibility vector column type:
    Uses native pgvector Vector(1536) on PostgreSQL.
    Uses JSON-serialized text on SQLite for local development and unit tests.
    """
    impl = Vector(1536)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(1536))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name != "postgresql":
            return json.dumps(value) if isinstance(value, (list, tuple)) else value
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name != "postgresql" and isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value
