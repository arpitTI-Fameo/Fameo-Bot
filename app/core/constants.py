"""
Domain constants and enumerations.

All magic values live here. Nothing is hardcoded in business logic.
"""

from __future__ import annotations

from enum import StrEnum, unique


# ---------------------------------------------------------------------------
# Entity statuses
# ---------------------------------------------------------------------------

@unique
class KnowledgeBaseStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DISABLED = "disabled"


@unique
class DocumentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    ARCHIVED = "archived"


@unique
class DocumentVersionStatus(StrEnum):
    PENDING = "pending"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    VERIFYING = "verifying"
    READY = "ready"
    FAILED = "failed"


@unique
class IngestionJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


@unique
class ConversationStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


@unique
class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ---------------------------------------------------------------------------
# RAG / Chat classification
# ---------------------------------------------------------------------------

@unique
class QueryCategory(StrEnum):
    KNOWLEDGE_QUERY = "knowledge_query"
    GENERAL_SUPPORT = "general_support"
    OUT_OF_SCOPE = "out_of_scope"
    ACCOUNT_SPECIFIC = "account_specific"
    UNKNOWN = "unknown"


@unique
class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

@unique
class LLMUsageStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------

@unique
class FeedbackReason(StrEnum):
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    INCORRECT = "incorrect"
    INCOMPLETE = "incomplete"
    OUT_OF_DATE = "out_of_date"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Pagination defaults
# ---------------------------------------------------------------------------

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------

CHARS_PER_TOKEN_ESTIMATE = 4  # Conservative estimate for token counting fallback
