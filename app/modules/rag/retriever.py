"""
Semantic retriever using pgvector.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.database.repositories.chunk import ChunkRepository
from app.modules.embeddings.service import EmbeddingService


class SemanticRetriever:
    """Retrieves document chunks using semantic search."""

    def __init__(self, repository: ChunkRepository, embedding_service: EmbeddingService):
        self._repository = repository
        self._embedding_service = embedding_service

    async def retrieve(
        self,
        query: str,
        *,
        version_ids: list[uuid.UUID] | None = None,
        top_k: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Embed the query and retrieve similar chunks.
        """
        query_embedding = await self._embedding_service.embed_query(query)
        
        results = await self._repository.semantic_search(
            embedding=query_embedding,
            version_ids=version_ids,
            top_k=top_k
        )
        return results
