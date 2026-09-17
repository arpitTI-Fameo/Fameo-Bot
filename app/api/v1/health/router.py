"""
Health and readiness endpoints.

GET /health — liveness: process is alive
GET /ready  — readiness: critical dependencies reachable
"""

from __future__ import annotations

from fastapi import APIRouter

from app.database.connection import check_database_health

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Liveness probe",
    description="Returns 200 if the process is alive. No dependency checks.",
    response_model=dict,
)
async def health() -> dict:
    return {"status": "healthy"}


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Returns 200 if critical dependencies are available.",
    response_model=dict,
)
async def ready() -> dict:
    checks: dict[str, bool] = {}

    # Database
    checks["database"] = await check_database_health()



    all_ready = all(checks.values())

    return {
        "status": "ready" if all_ready else "degraded",
        "checks": checks,
    }
