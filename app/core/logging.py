"""
Structured logging via structlog.

- JSON output in production, pretty console in development.
- Automatically binds request_id, trace_id, user_id when available.
- Filters secrets from log output.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog


# Patterns that must never appear in log values
_SECRET_PATTERNS = frozenset({
    "password", "secret", "token", "api_key", "apikey",
    "authorization", "credential", "service_role_key",
})


def _sanitize_event_dict(
    _logger: Any, _method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Redact values whose keys suggest they contain secrets."""
    for key in list(event_dict.keys()):
        if any(pat in key.lower() for pat in _SECRET_PATTERNS):
            event_dict[key] = "***REDACTED***"
    return event_dict


def setup_logging(log_level: str = "INFO", json_output: bool = False) -> None:
    """Configure structlog and stdlib logging together."""

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        _sanitize_event_dict,
    ]

    if json_output:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level.upper())

    # Quiet noisy libraries
    for name in ("uvicorn.access", "httpx", "httpcore", "asyncio"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a bound structured logger."""
    return structlog.get_logger(name)  # type: ignore[return-value]
