"""
Security utilities.

- HMAC-based service-to-service authentication
- User ID extraction from trusted internal headers
- Request signing and verification
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import TYPE_CHECKING

from app.core.exceptions import AuthenticationError, AuthorizationError

if TYPE_CHECKING:
    from fastapi import Request
    from app.core.config import SecuritySettings


# ---------------------------------------------------------------------------
# HMAC service-to-service auth
# ---------------------------------------------------------------------------

HMAC_TIMESTAMP_TOLERANCE_SECONDS = 300  # 5-minute window to prevent replay


def generate_service_token(
    secret: str,
    *,
    method: str = "POST",
    path: str = "/",
    timestamp: int | None = None,
) -> str:
    """
    Generate an HMAC-SHA256 service token.

    Format: ``{timestamp}.{hex_signature}``
    """
    ts = timestamp or int(time.time())
    payload = f"{method.upper()}:{path}:{ts}"
    sig = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{ts}.{sig}"


def verify_service_token(
    token: str,
    secret: str,
    *,
    method: str = "POST",
    path: str = "/",
    tolerance: int = HMAC_TIMESTAMP_TOLERANCE_SECONDS,
) -> bool:
    """
    Verify an HMAC service token. Checks signature and timestamp window.
    """
    parts = token.split(".", 1)
    if len(parts) != 2:
        return False

    try:
        ts = int(parts[0])
    except ValueError:
        return False

    # Replay window check
    now = int(time.time())
    if abs(now - ts) > tolerance:
        return False

    expected = generate_service_token(secret, method=method, path=path, timestamp=ts)
    return hmac.compare_digest(token, expected)


# ---------------------------------------------------------------------------
# Request-level auth helpers (used by dependencies)
# ---------------------------------------------------------------------------

def extract_user_id(request: "Request", settings: "SecuritySettings") -> str:
    """
    Extract user_id from a trusted internal header.
    Raises AuthenticationError if absent.
    """
    user_id = request.headers.get(settings.user_id_header)
    if not user_id or not user_id.strip():
        raise AuthenticationError("User identification is required.")
    return user_id.strip()


def verify_internal_request(
    request: "Request",
    settings: "SecuritySettings",
) -> None:
    """
    Verify that a request comes from a trusted internal service.
    Raises AuthenticationError on failure.
    """
    token = request.headers.get(settings.internal_auth_header)
    if not token:
        raise AuthenticationError("Internal service authentication required.")

    secret = settings.internal_service_secret.get_secret_value()
    method = request.method
    path = request.url.path

    if not verify_service_token(token, secret, method=method, path=path):
        raise AuthenticationError("Invalid or expired service token.")


def verify_admin_access(request: "Request") -> None:
    """
    Placeholder for admin-level authorization.
    In v1, admin endpoints require internal service auth only.
    Future: role-based checks.
    """
    # For now, admin = internal service. This is enforced at the dependency level.
    pass
