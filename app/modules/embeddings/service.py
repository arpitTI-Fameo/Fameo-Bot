"""
Embedding service facade.
"""

from __future__ import annotations

from app.modules.embeddings.interfaces import EmbeddingProvider
from app.core.config import EmbeddingSettings


class EmbeddingService:
    """Service for generating vector embeddings."""

    def __init__(self, provider: EmbeddingProvider, settings: EmbeddingSettings):
        self._provider = provider
        self._settings = settings

    @property
    def dimension(self) -> int:
        return self._provider.dimension

    @property
    def model_name(self) -> str:
        return self._provider.model_name
        
    @property
    def provider_name(self) -> str:
        return self._provider.provider_name

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        return await self._provider.embed_query(text)

    async def embed_chunks(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of chunk contents. Handles batching according to settings.
        """
        results: list[list[float]] = []
        batch_size = self._settings.batch_size
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = await self._provider.embed_documents(batch)
            results.extend(batch_embeddings)
            
        return results
