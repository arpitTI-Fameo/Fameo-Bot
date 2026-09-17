"""
Unit tests for security module.
"""

from __future__ import annotations

import time

from app.core.security import (
    generate_service_token,
    verify_service_token,
    HMAC_TIMESTAMP_TOLERANCE_SECONDS,
)


SECRET = "test-secret-key-for-hmac-minimum-32-chars"


class TestServiceToken:
    """Test HMAC service token generation and verification."""

    def test_valid_token(self):
        token = generate_service_token(SECRET, method="POST", path="/api/v1/chat")
        assert verify_service_token(
            token, SECRET, method="POST", path="/api/v1/chat"
        )

    def test_wrong_secret(self):
        token = generate_service_token(SECRET, method="POST", path="/api/v1/chat")
        assert not verify_service_token(
            token, "wrong-secret-key-for-test-minimum-32-c",
            method="POST", path="/api/v1/chat",
        )

    def test_wrong_method(self):
        token = generate_service_token(SECRET, method="POST", path="/api/v1/chat")
        assert not verify_service_token(
            token, SECRET, method="GET", path="/api/v1/chat"
        )

    def test_wrong_path(self):
        token = generate_service_token(SECRET, method="POST", path="/api/v1/chat")
        assert not verify_service_token(
            token, SECRET, method="POST", path="/api/v1/docs"
        )

    def test_expired_token(self):
        old_ts = int(time.time()) - HMAC_TIMESTAMP_TOLERANCE_SECONDS - 10
        token = generate_service_token(SECRET, method="POST", path="/", timestamp=old_ts)
        assert not verify_service_token(token, SECRET, method="POST", path="/")

    def test_malformed_token(self):
        assert not verify_service_token("no-dot-here", SECRET)
        assert not verify_service_token("abc.def", SECRET)
        assert not verify_service_token("", SECRET)

    def test_token_format(self):
        token = generate_service_token(SECRET, method="GET", path="/test")
        parts = token.split(".")
        assert len(parts) == 2
        # First part is timestamp (numeric)
        assert parts[0].isdigit()
        # Second part is hex signature
        assert len(parts[1]) == 64  # SHA256 hex
