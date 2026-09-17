"""
Local document ingestion script.
Reads a directory of PDFs, extracts text, chunks it, generates embeddings,
and stores them in the database.
"""

import asyncio
import os
from pathlib import Path
import uuid
import hashlib

from app.core.config import get_settings
from app.database.connection import init_database, get_session
from app.database.models import KnowledgeBase, Document, DocumentVersion, DocumentChunk
from app.modules.documents.parser import PyMuPDFParser
from app.modules.documents.chunker import SemanticChunker
from app.modules.embeddings.providers.sentence_transformers import SentenceTransformersProvider
from app.modules.embeddings.service import EmbeddingService
from app.core.logging import get_logger

logger = get_logger(__name__)


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


async def main():
    logger.info("starting_ingestion")
    settings = get_settings()
    
    # Initialize DB
    init_database(settings.database)
    
    # Setup Services
    parser = PyMuPDFParser()
    chunker = SemanticChunker(settings.chunk)
    provider = SentenceTransformersProvider()
    embedding_service = EmbeddingService(provider, settings.embedding)
    
    doc_dir = Path("doc/fameo Website KB")
    if not doc_dir.exists():
        logger.error("dir_not_found", path=str(doc_dir))
        return
        
    pdfs = list(doc_dir.glob("*.pdf"))
    logger.info("found_pdfs", count=len(pdfs))
    
    async with get_session() as session:
        # 1. Create or get Knowledge Base
        from sqlalchemy import select
        stmt = select(KnowledgeBase).where(KnowledgeBase.slug == "fameo-kb")
        result = await session.execute(stmt)
        kb = result.scalar_one_or_none()
        
        if not kb:
            kb = KnowledgeBase(
                name="Fameo Support KB",
                slug="fameo-kb",
                description="Imported from local docs",
                status="ACTIVE"
            )
            session.add(kb)
            await session.commit()
            await session.refresh(kb)
            
        logger.info("using_kb", kb_id=str(kb.id))
        
        # 2. Process each PDF
        for pdf_path in pdfs:
            logger.info("processing_file", file=pdf_path.name)
            file_hash = compute_file_hash(pdf_path)
            
            # Check if this document exists
            stmt = select(Document).where(Document.file_name == pdf_path.name, Document.knowledge_base_id == kb.id)
            result = await session.execute(stmt)
            doc = result.scalar_one_or_none()
            
            if not doc:
                doc = Document(
                    knowledge_base_id=kb.id,
                    name=pdf_path.stem,
                    file_name=pdf_path.name,
                    mime_type="application/pdf",
                    storage_path=f"local/{pdf_path.name}",
                    status="READY"
                )
                session.add(doc)
                await session.flush()
                
            # Create a new version
            version = DocumentVersion(
                document_id=doc.id,
                version_number=1, # simplified
                file_hash=file_hash,
                storage_path=doc.storage_path,
                embedding_provider=embedding_service.provider_name,
                embedding_model=embedding_service.model_name,
                embedding_dimension=embedding_service.dimension,
                status="PROCESSING"
            )
            session.add(version)
            await session.flush()
            
            doc.current_version_id = version.id
            
            # Parse & Chunk
            pages = parser.parse_file(str(pdf_path))
            version.page_count = len(pages)
            
            chunks = chunker.chunk_pages(pages)
            version.chunk_count = len(chunks)
            
            # Embed
            texts = [c.content for c in chunks]
            embeddings = await embedding_service.embed_chunks(texts)
            
            # Save Chunks
            for chunk_obj, emb in zip(chunks, embeddings):
                db_chunk = DocumentChunk(
                    document_version_id=version.id,
                    chunk_index=chunk_obj.chunk_index,
                    content=chunk_obj.content,
                    token_count=chunk_obj.token_count,
                    page_number=chunk_obj.page_number,
                    section=chunk_obj.section,
                    embedding=emb
                )
                session.add(db_chunk)
                
            version.status = "READY"
            await session.commit()
            logger.info("completed_file", file=pdf_path.name, chunks=len(chunks))

    logger.info("ingestion_complete")


if __name__ == "__main__":
    asyncio.run(main())
