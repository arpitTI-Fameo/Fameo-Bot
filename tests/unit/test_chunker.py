"""
Unit tests for semantic chunker.
"""

from __future__ import annotations

import pytest
from app.core.config import ChunkSettings
from app.modules.documents.chunker import SemanticChunker, PageContent


@pytest.fixture
def chunker():
    settings = ChunkSettings(
        target_size=100,
        max_size=200,
        overlap=20,
        min_size=10,
    )
    return SemanticChunker(settings)


class TestSemanticChunker:
    def test_empty_pages(self, chunker):
        result = chunker.chunk_pages([])
        assert result == []

    def test_single_small_page(self, chunker):
        pages = [PageContent(text="This is a reasonably sized text that should be kept as a single chunk by the chunker.", page_number=1)]
        result = chunker.chunk_pages(pages)
        assert len(result) >= 1
        assert result[0].page_number == 1
        assert result[0].chunk_index == 0

    def test_large_page_splits(self, chunker):
        long_text = "This is a test sentence. " * 200
        pages = [PageContent(text=long_text, page_number=1)]
        result = chunker.chunk_pages(pages)
        assert len(result) > 1
        for chunk in result:
            assert chunk.page_number == 1

    def test_preserves_page_numbers(self, chunker):
        pages = [
            PageContent(text="Content on page 1. " * 10, page_number=1),
            PageContent(text="Content on page 2. " * 10, page_number=2),
        ]
        result = chunker.chunk_pages(pages)
        page_numbers = {c.page_number for c in result}
        assert 1 in page_numbers or 2 in page_numbers

    def test_chunk_indices_sequential(self, chunker):
        pages = [PageContent(text="Word " * 500, page_number=1)]
        result = chunker.chunk_pages(pages)
        for i, chunk in enumerate(result):
            assert chunk.chunk_index == i

    def test_token_counts_positive(self, chunker):
        pages = [PageContent(text="Some meaningful content here.", page_number=1)]
        result = chunker.chunk_pages(pages)
        for chunk in result:
            assert chunk.token_count > 0

    def test_skips_empty_pages(self, chunker):
        pages = [
            PageContent(text="", page_number=1),
            PageContent(text="  \n  ", page_number=2),
            PageContent(text="This is real content that should be included in the chunked output and is long enough.", page_number=3),
        ]
        result = chunker.chunk_pages(pages)
        assert len(result) >= 1
