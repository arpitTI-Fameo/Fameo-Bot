"""
Token-budgeted context builder.

Constructs the LLM context from selected chunks while enforcing
a configurable token limit. Never sends the entire PDF to the LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.config import RAGSettings
from app.core.constants import CHARS_PER_TOKEN_ESTIMATE
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ContextSource:
    """A single source in the assembled context."""
    chunk_id: str
    document_id: str
    document_name: str
    version: int
    page: int | None
    section: str | None
    content: str
    relevance_score: float


@dataclass
class BuiltContext:
    """The assembled context for LLM generation."""
    text: str
    sources: list[ContextSource]
    total_tokens: int
    truncated: bool = False


class ContextBuilder:
    """
    Builds LLM context from ranked chunks within a token budget.

    Chunks are added in rank order until the budget is exhausted.
    Each chunk is formatted with source attribution for citation.
    """

    def __init__(self, settings: RAGSettings) -> None:
        self._token_limit = settings.context_token_limit

    def build(
        self,
        ranked_chunks: list[dict[str, Any]],
    ) -> BuiltContext:
        """
        Build context from ranked retrieval results.

        Args:
            ranked_chunks: Chunks sorted by relevance (best first).
                Each dict should contain: content, chunk_id, document_name,
                document_id, version, page_number, section, relevance_score.

        Returns:
            BuiltContext with formatted text, sources, and token count.
        """
        sources: list[ContextSource] = []
        context_parts: list[str] = []
        total_tokens = 0
        truncated = False

        for chunk in ranked_chunks:
            content = chunk.get("content", "")
            chunk_tokens = self._estimate_tokens(content)

            # Check budget
            if total_tokens + chunk_tokens > self._token_limit:
                # Try to fit a truncated version
                remaining = self._token_limit - total_tokens
                if remaining > 50:  # Worth including a partial chunk
                    content = self._truncate_to_tokens(content, remaining)
                    chunk_tokens = remaining
                    truncated = True
                else:
                    truncated = True
                    break

            # Format chunk with source attribution
            source = ContextSource(
                chunk_id=str(chunk.get("id", "")),
                document_id=str(chunk.get("document_id", "")),
                document_name=chunk.get("document_name", "Unknown"),
                version=chunk.get("version", 1),
                page=chunk.get("page_number"),
                section=chunk.get("section"),
                content=content,
                relevance_score=chunk.get("relevance_score", 0.0),
            )

            # Build formatted context block
            header = f"[Source: {source.document_name}"
            if source.page:
                header += f", Page {source.page}"
            if source.section:
                header += f", Section: {source.section}"
            header += "]"

            context_parts.append(f"{header}\n{content}")
            sources.append(source)
            total_tokens += chunk_tokens

        context_text = "\n\n---\n\n".join(context_parts)

        logger.info(
            "context_built",
            source_count=len(sources),
            total_tokens=total_tokens,
            truncated=truncated,
        )

        return BuiltContext(
            text=context_text,
            sources=sources,
            total_tokens=total_tokens,
            truncated=truncated,
        )

    def _estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // CHARS_PER_TOKEN_ESTIMATE)

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        max_chars = max_tokens * CHARS_PER_TOKEN_ESTIMATE
        if len(text) <= max_chars:
            return text
        # Truncate at word boundary
        truncated = text[:max_chars]
        last_space = truncated.rfind(" ")
        if last_space > max_chars * 0.8:
            truncated = truncated[:last_space]
        return truncated + "..."
