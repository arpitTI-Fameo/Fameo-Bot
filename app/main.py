"""
FastAPI application factory.

Creates the app with proper lifecycle management, middleware, and routing.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.middleware import setup_middleware
from app.core.telemetry import setup_telemetry
from app.database.connection import init_database, close_database
from app.api.v1.router import v1_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle: startup → yield → shutdown."""
    settings = get_settings()

    # Startup
    init_database(settings.database)

    yield

    # Shutdown
    await close_database()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="AI Support Bot API",
        description="Production-grade AI Support Backend with RAG over document knowledge bases.",
        version="0.1.0",
        docs_url="/docs" if settings.app.is_development else None,
        redoc_url="/redoc" if settings.app.is_development else None,
        lifespan=lifespan,
    )

    # Logging
    setup_logging(
        log_level=settings.app.log_level,
        json_output=settings.app.is_production,
    )

    # Middleware
    setup_middleware(app, settings.app.cors_origins)

    # Telemetry
    setup_telemetry(app, settings.observability)

    # Routers
    app.include_router(v1_router)

    return app


# Uvicorn entry point
app = create_app()
