"""
Database engine / session bootstrap.

Reads connection info from the DATABASE_URL env var, falling back to a local
Postgres instance. Swap the driver (psycopg2 / asyncpg / etc.) as needed.
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=False, future=True, pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI-style dependency / generator for a request-scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context-manager style session for scripts / background jobs."""
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
    """Create all tables. Intended for local/dev/PoC use (use Alembic in prod)."""
    from app.models import (  # noqa: F401  (ensures models are registered on Base)
        organization,
        user,
        umkm_profile,
        lender_profile,
        qris_transaction,
        score,
        loan_outcome,
        match,
        audit_log,
    )

    Base.metadata.create_all(bind=engine)