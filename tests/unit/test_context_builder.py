"""
Unit tests for context builder.
"""

from __future__ import annotations

from app.core.config import RAGSettings
from app.modules.rag.context_builder import ContextBuilder


class TestContextBuilder:
    def setup_method(self):
        settings = RAGSettings(context_token_limit=500)
        self.builder = ContextBuilder(settings)

    def test_empty_chunks(self):
        result = self.builder.build([])
        assert result.text == ""
        assert result.sources == []
        assert result.total_tokens == 0

    def test_single_chunk(self):
        chunks = [{
            "id": "chunk-1",
            "content": "This is some content about cancellation policy.",
            "document_id": "doc-1",
            "document_name": "User Guide",
            "version": 1,
            "page_number": 5,
            "section": "Cancellation",
            "relevance_score": 0.92,
        }]
        result = self.builder.build(chunks)
        assert len(result.sources) == 1
        assert "User Guide" in result.text
        assert "Page 5" in result.text
        assert "Cancellation" in result.text
        assert "cancellation policy" in result.text

    def test_token_budget_enforced(self):
        # Create chunks that exceed the budget
        chunks = [
            {
                "id": f"chunk-{i}",
                "content": "Word " * 500,  # ~500 tokens each
                "document_id": "doc-1",
                "document_name": "Big Doc",
                "version": 1,
                "page_number": i,
                "section": None,
                "relevance_score": 0.9 - i * 0.1,
            }
            for i in range(5)
        ]
        result = self.builder.build(chunks)
        # Should not include all chunks
        assert len(result.sources) < 5
        assert result.total_tokens <= 550  # Some tolerance

    def test_sources_contain_metadata(self):
        chunks = [{
            "id": "c1",
            "content": "Test content",
            "document_id": "d1",
            "document_name": "FAQ",
            "version": 2,
            "page_number": 3,
            "section": "Billing",
            "relevance_score": 0.85,
        }]
        result = self.builder.build(chunks)
        source = result.sources[0]
        assert source.document_name == "FAQ"
        assert source.version == 2
        assert source.page == 3
        assert source.section == "Billing"
        assert source.relevance_score == 0.85

    def test_truncation_flag(self):
        # Single chunk that exceeds budget
        chunks = [{
            "id": "big",
            "content": "Word " * 2000,
            "document_id": "d1",
            "document_name": "Huge",
            "version": 1,
            "page_number": 1,
            "section": None,
            "relevance_score": 0.9,
        }]
        result = self.builder.build(chunks)
        assert result.truncated is True
