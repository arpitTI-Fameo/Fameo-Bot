"""
KnowledgeBase model — top-level container for document collections.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import KnowledgeBaseStatus
from app.database.base import Base, UUIDMixin, TimestampMixin


class KnowledgeBase(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_bases"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=KnowledgeBaseStatus.ACTIVE
    )

    # Relationships
    documents: Mapped[list["Document"]] = relationship(  # type: ignore[name-defined]
        "Document", back_populates="knowledge_base", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_knowledge_bases_status", "status"),
    )
