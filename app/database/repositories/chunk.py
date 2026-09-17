"""
DocumentChunk repository — vector search and chunk management.
"""

from __future__ import annotations

import uuid
from typing import Any, Sequence

from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.document_chunk import DocumentChunk
from app.database.repositories.base import BaseRepository


class ChunkRepository(BaseRepository[DocumentChunk]):
    model_class = DocumentChunk

    async def semantic_search(
        self,
        embedding: list[float],
        *,
        version_ids: list[uuid.UUID] | None = None,
        top_k: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Perform cosine similarity search using pgvector.

        Returns list of dicts with chunk data and similarity_score.
        """
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

        # Build query with cosine distance operator (<=>)
        query = text("""
            SELECT
                dc.id,
                dc.document_version_id,
                dc.chunk_index,
                dc.content,
                dc.token_count,
                dc.page_number,
                dc.section,
                dc.metadata,
                1 - (dc.embedding <=> CAST(:embedding AS vector)) AS similarity_score
            FROM document_chunks dc
            WHERE dc.embedding IS NOT NULL
            {version_filter}
            ORDER BY dc.embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
        """.format(
            version_filter=(
                "AND dc.document_version_id = ANY(:version_ids)"
                if version_ids else ""
            )
        ))

        params: dict[str, Any] = {
            "embedding": embedding_str,
            "top_k": top_k,
        }
        if version_ids:
            params["version_ids"] = [str(v) for v in version_ids]

        result = await self.session.execute(query, params)
        rows = result.mappings().all()
        return [dict(row) for row in rows]

    async def keyword_search(
        self,
        query_text: str,
        *,
        version_ids: list[uuid.UUID] | None = None,
        top_k: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Full-text search using PostgreSQL tsvector/tsquery.
        """
        search_query = text("""
            SELECT
                dc.id,
                dc.document_version_id,
                dc.chunk_index,
                dc.content,
                dc.token_count,
                dc.page_number,
                dc.section,
                dc.metadata,
                ts_rank_cd(
                    to_tsvector('english', dc.content),
                    plainto_tsquery('english', :query)
                ) AS text_rank
            FROM document_chunks dc
            WHERE to_tsvector('english', dc.content) @@ plainto_tsquery('english', :query)
            {version_filter}
            ORDER BY text_rank DESC
            LIMIT :top_k
        """.format(
            version_filter=(
                "AND dc.document_version_id = ANY(:version_ids)"
                if version_ids else ""
            )
        ))

        params: dict[str, Any] = {
            "query": query_text,
            "top_k": top_k,
        }
        if version_ids:
            params["version_ids"] = [str(v) for v in version_ids]

        result = await self.session.execute(search_query, params)
        rows = result.mappings().all()
        return [dict(row) for row in rows]

    async def get_by_version(
        self, version_id: uuid.UUID
    ) -> Sequence[DocumentChunk]:
        """Get all chunks for a document version, ordered by index."""
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_version_id == version_id)
            .order_by(DocumentChunk.chunk_index)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_by_version(self, version_id: uuid.UUID) -> int:
        """Delete all chunks for a version. Returns count deleted."""
        from sqlalchemy import delete as sa_delete
        stmt = (
            sa_delete(DocumentChunk)
            .where(DocumentChunk.document_version_id == version_id)
        )
        result = await self.session.execute(stmt)
        return result.rowcount  # type: ignore[return-value]
