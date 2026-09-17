"""
Shared test configuration and fixtures.
"""

from __future__ import annotations

import os
import pytest

# Set test environment before any app imports
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("GEMINI_API_KEY", "AIzaSy_test_key_not_real")
os.environ.setdefault("INTERNAL_SERVICE_SECRET", "test-internal-secret-minimum-32-characters-long")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")


@pytest.fixture
def anyio_backend():
    return "asyncio"
