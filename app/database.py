"""
Database engine / session bootstrap.

Uses Supabase Session Pooler for PostgreSQL connections.
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


_engine_kwargs = {"echo": False, "pool_pre_ping": True}

if not settings.DATABASE_URL.startswith("sqlite"):
    # pool_size / max_overflow / pool_recycle only apply to QueuePool
    # (Postgres). SQLite uses SingletonThreadPool and rejects these kwargs.
    _engine_kwargs.update(
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800,
    )

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""

    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency with a request-scoped database session."""

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context-manager session for scripts and background jobs."""

    db = SessionLocal()

    try:
        yield db
        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def init_db() -> None:
    """
    Create all tables.

    Intended for local development and PoC usage.
    Use Alembic migrations for production.
    """

    Base.metadata.create_all(bind=engine)