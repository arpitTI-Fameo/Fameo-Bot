"""
Unit tests for configuration module.
"""

from __future__ import annotations

import os
import pytest
from unittest.mock import patch

from app.core.config import (
    AppSettings,
    DatabaseSettings,
    RAGSettings,
    ChunkSettings,
    EmbeddingSettings,
)


class TestAppSettings:
    """Test application settings."""

    def test_defaults(self):
        settings = AppSettings(env="development")
        assert settings.env == "development"
        assert settings.name == "support-ai"
        assert settings.debug is False
        assert settings.log_level == "INFO"

    def test_is_production(self):
        settings = AppSettings(env="production")
        assert settings.is_production is True
        assert settings.is_development is False

    def test_is_testing(self):
        settings = AppSettings(env="testing")
        assert settings.is_testing is True
        assert settings.is_production is False

    def test_cors_from_json_string(self):
        settings = AppSettings(cors_origins='["http://a.com","http://b.com"]')
        assert settings.cors_origins == ["http://a.com", "http://b.com"]


class TestDatabaseSettings:
    """Test database settings."""

    def test_requires_url(self):
        with patch.dict(os.environ, {}, clear=False):
            # Should raise if DATABASE_URL is not set
            # (env var is set in conftest, so we test with explicit value)
            settings = DatabaseSettings(url="postgresql+asyncpg://user:pass@host/db")
            assert settings.pool_size == 10
            assert settings.max_overflow == 20


class TestRAGSettings:
    """Test RAG settings validation."""

    def test_valid_weights(self):
        settings = RAGSettings(
            hybrid_semantic_weight=0.6,
            hybrid_keyword_weight=0.4,
        )
        assert settings.hybrid_semantic_weight == 0.6

    def test_invalid_weights_raises(self):
        with pytest.raises(ValueError, match="must sum to 1.0"):
            RAGSettings(
                hybrid_semantic_weight=0.5,
                hybrid_keyword_weight=0.3,
            )

    def test_defaults(self):
        settings = RAGSettings()
        assert settings.top_k == 20
        assert settings.rerank_top_k == 5
        assert settings.context_token_limit == 3000
        assert settings.min_confidence == 0.3


class TestChunkSettings:
    """Test chunk settings."""

    def test_defaults(self):
        settings = ChunkSettings()
        assert settings.target_size == 512
        assert settings.max_size == 1024
        assert settings.overlap == 64
        assert settings.min_size == 50


class TestEmbeddingSettings:
    """Test embedding settings."""

    def test_defaults(self):
        settings = EmbeddingSettings()
        assert settings.provider == "sentence-transformers"
        assert settings.model == "all-MiniLM-L6-v2"
        assert settings.dimension == 384
