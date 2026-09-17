"""
Unit tests for prompt loader.
"""

from __future__ import annotations

import pytest
from app.modules.llm.prompts.loader import (
    load_prompt,
    get_support_system_prompt,
    get_summary_prompt,
)


class TestPromptLoader:
    def test_load_support_system(self):
        prompt = get_support_system_prompt(
            context="Test context here",
            history="User: hi\nAssistant: hello",
            question="What is the policy?",
        )
        assert "Test context here" in prompt
        assert "What is the policy?" in prompt
        assert "CONTEXT" in prompt

    def test_load_summary_prompt(self):
        prompt = get_summary_prompt(
            conversation="User: How do refunds work?\nAssistant: Refunds take 5 days."
        )
        assert "How do refunds work?" in prompt
        assert "SUMMARY" in prompt

    def test_missing_template_raises(self):
        with pytest.raises(FileNotFoundError):
            load_prompt("nonexistent_template.txt")

    def test_variable_substitution(self):
        prompt = get_support_system_prompt(
            context="<CTX>",
            history="<HIST>",
            question="<Q>",
        )
        assert "<CTX>" in prompt
        assert "<HIST>" in prompt
        assert "<Q>" in prompt
        # Placeholders should be replaced
        assert "{context}" not in prompt
        assert "{history}" not in prompt
        assert "{question}" not in prompt
