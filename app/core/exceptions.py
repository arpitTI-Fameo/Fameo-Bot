"""
Domain exception hierarchy.

Every exception carries a machine-readable error code, an HTTP status, and a
user-safe message. Internal details stay in logs, never in responses.
"""

from __future__ import annotations

from typing import Any


class SupportAIError(Exception):
    """Base exception for the entire application."""

    error_code: str = "INTERNAL_ERROR"
    status_code: int = 500
    message: str = "An internal error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        error_code: str | None = None,
        status_code: int | None = None,
        detail: Any = None,
    ) -> None:
        self.message = message or self.__class__.message
        if error_code:
            self.error_code = error_code
        if status_code:
            self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# Client errors (4xx)
# ---------------------------------------------------------------------------

class ValidationError(SupportAIError):
    error_code = "VALIDATION_ERROR"
    status_code = 422
    message = "Request validation failed."


class NotFoundError(SupportAIError):
    error_code = "NOT_FOUND"
    status_code = 404
    message = "The requested resource was not found."


class ConflictError(SupportAIError):
    error_code = "CONFLICT"
    status_code = 409
    message = "The resource already exists or conflicts with current state."


class AuthenticationError(SupportAIError):
    error_code = "AUTHENTICATION_FAILED"
    status_code = 401
    message = "Authentication is required."


class AuthorizationError(SupportAIError):
    error_code = "FORBIDDEN"
    status_code = 403
    message = "You do not have permission to perform this action."


class RateLimitError(SupportAIError):
    error_code = "RATE_LIMITED"
    status_code = 429
    message = "Too many requests. Please try again later."


class FileTooLargeError(SupportAIError):
    error_code = "FILE_TOO_LARGE"
    status_code = 413
    message = "The uploaded file exceeds the maximum allowed size."


class InvalidFileTypeError(SupportAIError):
    error_code = "INVALID_FILE_TYPE"
    status_code = 415
    message = "The uploaded file type is not supported."


# ---------------------------------------------------------------------------
# Infrastructure / provider errors (5xx)
# ---------------------------------------------------------------------------

class DatabaseError(SupportAIError):
    error_code = "DATABASE_ERROR"
    status_code = 503
    message = "A database error occurred."


class StorageError(SupportAIError):
    error_code = "STORAGE_ERROR"
    status_code = 503
    message = "A storage error occurred."


class CacheError(SupportAIError):
    error_code = "CACHE_ERROR"
    status_code = 503
    message = "A cache error occurred."


# ---------------------------------------------------------------------------
# LLM / RAG errors
# ---------------------------------------------------------------------------

class LLMError(SupportAIError):
    error_code = "LLM_ERROR"
    status_code = 502
    message = "The language model service is temporarily unavailable."


class LLMTimeoutError(LLMError):
    error_code = "LLM_TIMEOUT"
    message = "The language model request timed out."


class LLMRateLimitError(LLMError):
    error_code = "LLM_RATE_LIMITED"
    status_code = 429
    message = "The language model rate limit has been reached."


class EmbeddingError(SupportAIError):
    error_code = "EMBEDDING_ERROR"
    status_code = 502
    message = "The embedding service is temporarily unavailable."


class RetrievalError(SupportAIError):
    error_code = "RAG_RETRIEVAL_FAILED"
    status_code = 502
    message = "Unable to retrieve support information."


class ContextOverflowError(SupportAIError):
    error_code = "CONTEXT_OVERFLOW"
    status_code = 500
    message = "The constructed context exceeds token limits."


# ---------------------------------------------------------------------------
# Ingestion errors
# ---------------------------------------------------------------------------

class IngestionError(SupportAIError):
    error_code = "INGESTION_ERROR"
    status_code = 500
    message = "Document ingestion failed."


class DocumentParsingError(IngestionError):
    error_code = "DOCUMENT_PARSING_ERROR"
    message = "Failed to parse the document."


class DocumentCleaningError(IngestionError):
    error_code = "DOCUMENT_CLEANING_ERROR"
    message = "Failed to clean the document content."


class ChunkingError(IngestionError):
    error_code = "CHUNKING_ERROR"
    message = "Failed to chunk the document."
