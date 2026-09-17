"""
Observability / telemetry setup.

- OpenTelemetry tracing (opt-in via config)
- Prometheus metrics
- Application-level metric counters
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from prometheus_client import Counter, Histogram, Info

if TYPE_CHECKING:
    from fastapi import FastAPI
    from app.core.config import ObservabilitySettings


# ---------------------------------------------------------------------------
# Prometheus metrics — declared once, used throughout the app
# ---------------------------------------------------------------------------

APP_INFO = Info("support_ai", "AI Support Bot application info")

REQUEST_COUNT = Counter(
    "support_ai_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "support_ai_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

LLM_REQUEST_COUNT = Counter(
    "support_ai_llm_requests_total",
    "Total LLM provider requests",
    ["provider", "model", "status"],
)

LLM_LATENCY = Histogram(
    "support_ai_llm_duration_seconds",
    "LLM request latency",
    ["provider", "model"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

LLM_TOKENS = Counter(
    "support_ai_llm_tokens_total",
    "Total LLM tokens consumed",
    ["provider", "model", "token_type"],
)

EMBEDDING_LATENCY = Histogram(
    "support_ai_embedding_duration_seconds",
    "Embedding generation latency",
    ["provider", "model"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

RETRIEVAL_LATENCY = Histogram(
    "support_ai_retrieval_duration_seconds",
    "RAG retrieval latency",
    ["retrieval_type"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

INGESTION_DURATION = Histogram(
    "support_ai_ingestion_duration_seconds",
    "Document ingestion pipeline duration",
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

INGESTION_ERRORS = Counter(
    "support_ai_ingestion_errors_total",
    "Total ingestion pipeline errors",
    ["error_code"],
)

DB_LATENCY = Histogram(
    "support_ai_db_duration_seconds",
    "Database query latency",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
)


# ---------------------------------------------------------------------------
# OpenTelemetry setup (conditional)
# ---------------------------------------------------------------------------

def setup_telemetry(app: "FastAPI", settings: "ObservabilitySettings") -> None:
    """Configure OpenTelemetry tracing if enabled."""
    APP_INFO.info({"version": "0.1.0", "environment": "configured"})

    if not settings.otel_enabled:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        resource = Resource.create({"service.name": settings.otel_service_name})
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(app)
        SQLAlchemyInstrumentor().instrument()
        HTTPXClientInstrumentor().instrument()

    except ImportError:
        import logging
        logging.getLogger(__name__).warning(
            "OpenTelemetry packages not available; tracing disabled"
        )
