"""
Unit tests for document cleaner.
"""

from __future__ import annotations

from app.modules.documents.cleaner import DocumentCleaner


class TestDocumentCleaner:
    def setup_method(self):
        self.cleaner = DocumentCleaner()

    def test_empty_string(self):
        assert self.cleaner.clean("") == ""

    def test_normalize_whitespace(self):
        text = "Hello   World\t\there"
        result = self.cleaner.clean(text)
        assert "  " not in result
        assert "\t" not in result

    def test_remove_page_numbers(self):
        text = "Some content\n42\nMore content"
        result = self.cleaner.clean(text)
        assert "42" not in result.split("\n")

    def test_remove_page_x_of_y(self):
        text = "Content here Page 3 of 10 more content"
        result = self.cleaner.clean(text)
        assert "Page 3 of 10" not in result

    def test_normalize_unicode(self):
        text = "He said \u201chello\u201d and she\u2019s here"
        result = self.cleaner.clean(text)
        assert '"hello"' in result
        assert "she's" in result

    def test_collapse_newlines(self):
        text = "First\n\n\n\n\nSecond"
        result = self.cleaner.clean(text)
        assert "\n\n\n" not in result
        assert "\n\n" in result

    def test_preserves_meaningful_content(self):
        text = "This is a meaningful paragraph.\n\nThis is another one."
        result = self.cleaner.clean(text)
        assert "meaningful paragraph" in result
        assert "another one" in result
