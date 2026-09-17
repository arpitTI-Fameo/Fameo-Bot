"""
Embedding provider interfaces — protocol-based abstraction.

Any embedding backend (Sentence Transformers, OpenAI, Cohere, etc.)
implements this protocol and becomes swappable via config.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for embedding providers."""

    @property
    def dimension(self) -> int:
        """Return the embedding dimension for this model."""
        ...

    @property
    def model_name(self) -> str:
        """Return the model identifier."""
        ...

    @property
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'sentence-transformers', 'openai')."""
        ...

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a batch of document chunks.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (each a list of floats).
        """
        ...

    async def embed_query(self, text: str) -> list[float]:
        """
        Generate an embedding for a single query string.

        Some providers use different models/settings for queries vs. documents.

        Args:
            text: Query text.

        Returns:
            Embedding vector.
        """
        ...
