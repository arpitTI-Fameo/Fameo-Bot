"""
Document model — represents a source document within a knowledge base.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DocumentStatus
from app.database.base import Base, UUIDMixin, TimestampMixin


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"

    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=DocumentStatus.PENDING
    )
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_versions.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )

    # Relationships
    knowledge_base: Mapped["KnowledgeBase"] = relationship(  # type: ignore[name-defined]
        "KnowledgeBase", back_populates="documents"
    )
    versions: Mapped[list["DocumentVersion"]] = relationship(  # type: ignore[name-defined]
        "DocumentVersion",
        back_populates="document",
        foreign_keys="DocumentVersion.document_id",
        lazy="selectin",
        order_by="DocumentVersion.version_number.desc()",
    )
    ingestion_jobs: Mapped[list["IngestionJob"]] = relationship(  # type: ignore[name-defined]
        "IngestionJob",
        back_populates="document",
        foreign_keys="IngestionJob.document_id",
        lazy="noload",
    )

    __table_args__ = (
        Index("ix_documents_kb_status", "knowledge_base_id", "status"),
        Index("ix_documents_status", "status"),
    )
