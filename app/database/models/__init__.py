"""
Database models package — import all models for Alembic discovery.
"""

from app.database.models.knowledge_base import KnowledgeBase
from app.database.models.document import Document
from app.database.models.document_version import DocumentVersion
from app.database.models.document_chunk import DocumentChunk

__all__ = [
    "KnowledgeBase",
    "Document",
    "DocumentVersion",
    "DocumentChunk",
]
