"""
Strongly-typed, hierarchical application configuration.

All infrastructure knobs live here — no hardcoded values elsewhere.
Pydantic Settings validates at startup; the app fails-fast on missing/invalid config.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Top-level application settings."""

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    env: str = Field(default="development", description="Runtime environment")
    name: str = Field(default="support-ai")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default=1)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v  # type: ignore[return-value]

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        return self.env == "development"

    @property
    def is_testing(self) -> bool:
        return self.env == "testing"


class DatabaseSettings(BaseSettings):
    """PostgreSQL / asyncpg connection settings."""

    model_config = SettingsConfigDict(env_prefix="DATABASE_", env_file=".env", extra="ignore")

    url: SecretStr = Field(..., description="postgresql+asyncpg://...")
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)
    pool_timeout: int = Field(default=30)
    echo: bool = Field(default=False)


class SupabaseSettings(BaseSettings):
    """Supabase project settings."""

    model_config = SettingsConfigDict(env_prefix="SUPABASE_", env_file=".env", extra="ignore")

    url: str = Field(..., description="Supabase project URL")
    service_role_key: SecretStr = Field(..., description="Service role key (server-side only)")
    storage_bucket: str = Field(default="support-documents")


class RedisSettings(BaseSettings):
    """Redis connection settings."""

    model_config = SettingsConfigDict(env_prefix="REDIS_", env_file=".env", extra="ignore")

    url: SecretStr = Field(default=SecretStr("redis://localhost:6379/0"))
    key_prefix: str = Field(default="support-ai:")
    default_ttl: int = Field(default=3600, description="Default TTL in seconds")


class GroqSettings(BaseSettings):
    """Groq LLM provider settings."""

    model_config = SettingsConfigDict(env_prefix="GROQ_", env_file=".env", extra="ignore")

    api_key: SecretStr = Field(..., description="Groq API key")
    model: str = Field(default="llama-3.1-70b-versatile")
    max_tokens: int = Field(default=2048)
    temperature: float = Field(default=0.1)
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3)


class EmbeddingSettings(BaseSettings):
    """Embedding provider settings."""

    model_config = SettingsConfigDict(env_prefix="EMBEDDING_", env_file=".env", extra="ignore")

    provider: str = Field(default="sentence-transformers")
    model: str = Field(default="all-MiniLM-L6-v2")
    dimension: int = Field(default=384)
    batch_size: int = Field(default=64)


class RAGSettings(BaseSettings):
    """RAG retrieval pipeline settings."""

    model_config = SettingsConfigDict(env_prefix="RAG_", env_file=".env", extra="ignore")

    top_k: int = Field(default=20, description="Initial retrieval count")
    rerank_top_k: int = Field(default=5, description="Post-rerank count")
    context_token_limit: int = Field(default=1000)
    min_confidence: float = Field(default=0.3)
    hybrid_semantic_weight: float = Field(default=0.7)
    hybrid_keyword_weight: float = Field(default=0.3)

    @model_validator(mode="after")
    def validate_weights(self) -> "RAGSettings":
        total = self.hybrid_semantic_weight + self.hybrid_keyword_weight
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Hybrid weights must sum to 1.0, got {total}")
        return self


class ChunkSettings(BaseSettings):
    """Document chunking settings."""

    model_config = SettingsConfigDict(env_prefix="CHUNK_", env_file=".env", extra="ignore")

    target_size: int = Field(default=512, description="Target chunk size in tokens")
    max_size: int = Field(default=1024)
    overlap: int = Field(default=64)
    min_size: int = Field(default=50)


class RateLimitSettings(BaseSettings):
    """Rate limiting settings."""

    model_config = SettingsConfigDict(env_prefix="RATE_LIMIT_", env_file=".env", extra="ignore")

    enabled: bool = Field(default=True)
    chat_per_minute: int = Field(default=20)
    upload_per_hour: int = Field(default=10)
    global_concurrent: int = Field(default=100)


class WorkerSettings(BaseSettings):
    """Celery worker settings."""

    model_config = SettingsConfigDict(env_prefix="CELERY_", env_file=".env", extra="ignore")

    broker_url: SecretStr = Field(default=SecretStr("redis://localhost:6379/1"))
    result_backend: SecretStr = Field(default=SecretStr("redis://localhost:6379/2"))
    worker_concurrency: int = Field(default=4)
    task_max_retries: int = Field(default=3)


class StorageSettings(BaseSettings):
    """File upload / storage settings."""

    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

    max_upload_size_mb: int = Field(default=50)
    allowed_mime_types: list[str] = Field(
        default_factory=lambda: ["application/pdf"]
    )
    storage_path_prefix: str = Field(default="documents")

    @field_validator("allowed_mime_types", mode="before")
    @classmethod
    def parse_mimes(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v  # type: ignore[return-value]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


class SecuritySettings(BaseSettings):
    """Security and service-auth settings."""

    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

    internal_service_secret: SecretStr = Field(
        ..., description="Shared secret for HMAC service-to-service auth (≥32 chars)"
    )
    api_key_header: str = Field(default="X-API-Key")
    internal_auth_header: str = Field(default="X-Service-Auth")
    user_id_header: str = Field(default="X-User-ID")


class ObservabilitySettings(BaseSettings):
    """OpenTelemetry and metrics settings."""

    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

    otel_enabled: bool = Field(default=False)
    otel_service_name: str = Field(default="support-ai")
    otel_exporter_endpoint: str = Field(default="http://localhost:4317")
    metrics_enabled: bool = Field(default=True)
    metrics_port: int = Field(default=9090)


class Settings:
    """Aggregated settings — single access point for all configuration categories."""

    def __init__(self) -> None:
        self.app = AppSettings()
        self.database = DatabaseSettings()
        self.supabase = SupabaseSettings()
        self.redis = RedisSettings()
        self.groq = GroqSettings()
        self.embedding = EmbeddingSettings()
        self.rag = RAGSettings()
        self.chunk = ChunkSettings()
        self.rate_limit = RateLimitSettings()
        self.worker = WorkerSettings()
        self.storage = StorageSettings()
        self.security = SecuritySettings()
        self.observability = ObservabilitySettings()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton settings factory. Cached after first call."""
    return Settings()
