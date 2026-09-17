"""
FastAPI dependency injection.

Provides database sessions, settings, and auth dependencies for route handlers.
All dependencies are async-compatible and testable via overrides.
"""

from __future__ import annotations

from typing import Annotated, AsyncGenerator

from fastapi import Depends, Request

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError
from app.core.security import extract_user_id, verify_internal_request


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def get_app_settings() -> Settings:
    """Provide the application settings singleton."""
    return get_settings()


SettingsDep = Annotated[Settings, Depends(get_app_settings)]


# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------

async def get_db_session(
    settings: SettingsDep,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async DB session per request.
    Commits on success, rolls back on exception.
    """
    from app.database.connection import get_session_factory

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


DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


# ---------------------------------------------------------------------------
# Authentication dependencies
# ---------------------------------------------------------------------------

async def require_user(
    request: Request,
    settings: SettingsDep,
) -> str:
    """
    Extract and return the user_id from the request.
    For v1, trusts the internal header set by the Node.js gateway.
    Requires internal service auth OR a valid API key.
    """
    user_id = request.headers.get(settings.security.user_id_header)
    if not user_id or not user_id.strip():
        raise AuthenticationError("User identification is required.")
    return user_id.strip()


UserIdDep = Annotated[str, Depends(require_user)]


async def require_internal_service(
    request: Request,
    settings: SettingsDep,
) -> None:
    """
    Verify this request comes from a trusted internal service (Node.js backend).
    """
    verify_internal_request(request, settings.security)


InternalAuthDep = Annotated[None, Depends(require_internal_service)]


async def require_admin(
    request: Request,
    settings: SettingsDep,
) -> None:
    """
    Admin endpoints require internal service auth.
    Future: add role-based checks.
    """
    verify_internal_request(request, settings.security)


AdminAuthDep = Annotated[None, Depends(require_admin)]
