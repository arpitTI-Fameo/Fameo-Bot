"""
API v1 router aggregator.

All v1 sub-routers are mounted here under /api/v1.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.health.router import router as health_router

v1_router = APIRouter(prefix="/api/v1")

from app.api.v1.chat.router import router as chat_router

# Health (no auth)
v1_router.include_router(health_router)

# Chat endpoints
v1_router.include_router(chat_router, prefix="/chat")


