"""
DocumentVersion model — tracks versioned processing of a document.
Each version has its own chunks and embeddings.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DocumentVersionStatus
from app.database.base import Base, UUIDMixin


class DocumentVersion(Base, UUIDMixin):
    __tablename__ = "document_versions"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding_provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    embedding_dimension: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=DocumentVersionStatus.PENDING
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    document: Mapped["Document"] = relationship(  # type: ignore[name-defined]
        "Document",
        back_populates="versions",
        foreign_keys=[document_id],
    )
    chunks: Mapped[list["DocumentChunk"]] = relationship(  # type: ignore[name-defined]
        "DocumentChunk",
        back_populates="document_version",
        lazy="noload",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_doc_version"),
        Index("ix_doc_versions_doc_status", "document_id", "status"),
        Index("ix_doc_versions_hash", "file_hash"),
    )
