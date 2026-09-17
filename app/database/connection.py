"""
Async database connection management.

- Creates async SQLAlchemy engine with asyncpg
- Session factory with proper lifecycle
- Connection health check
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text

from app.core.config import DatabaseSettings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Module-level singletons — initialized by init_database()
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_database(settings: DatabaseSettings) -> None:
    """
    Initialize the async engine and session factory.
    Called once at application startup.
    """
    global _engine, _session_factory

    _engine = create_async_engine(
        settings.url.get_secret_value(),
        pool_size=settings.pool_size,
        max_overflow=settings.max_overflow,
        pool_timeout=settings.pool_timeout,
        pool_pre_ping=True,
        echo=settings.echo,
    )

    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    logger.info("database_initialized", pool_size=settings.pool_size)


def get_engine() -> AsyncEngine:
    """Get the async engine. Raises if not initialized."""
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get the session factory. Raises if not initialized."""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _session_factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.
    Commits on success, rolls back on exception.
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.
    Unlike get_session, this is a raw generator (no @asynccontextmanager).
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def check_database_health() -> bool:
    """Run a simple query to verify database connectivity."""
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.warning("database_health_check_failed")
        return False


async def close_database() -> None:
    """Dispose of the engine connection pool. Called at shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        logger.info("database_connection_closed")
    _engine = None
    _session_factory = None
