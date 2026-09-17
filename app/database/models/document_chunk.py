"""
DocumentChunk model — stores chunked document content with vector embeddings.

Uses pgvector for the embedding column.
Unique constraint on (document_version_id, chunk_index) ensures idempotent insertion.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDMixin


class DocumentChunk(Base, UUIDMixin):
    __tablename__ = "document_chunks"

    document_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict
    )

    # pgvector embedding — dimension is set dynamically via migration
    # Using raw column definition; the actual VECTOR type is applied in migration
    # We store as a Python list and let pgvector handle serialization
    from pgvector.sqlalchemy import Vector
    embedding: Mapped[list[float] | None] = mapped_column(Vector, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    document_version: Mapped["DocumentVersion"] = relationship(  # type: ignore[name-defined]
        "DocumentVersion", back_populates="chunks"
    )

    __table_args__ = (
        # Idempotency: prevent duplicate chunks for the same version
        UniqueConstraint(
            "document_version_id", "chunk_index",
            name="uq_chunk_version_index",
        ),
        Index("ix_chunks_version", "document_version_id"),
        Index("ix_chunks_page", "page_number"),
        # HNSW vector index is created in the migration, not here,
        # because it requires the pgvector extension and specific ops class.
        # Full-text search GIN index is also created in migration.
    )
