"""
Prompt template loader.

Loads prompt templates from the prompts/ directory with variable substitution.
Templates are cached after first load.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "prompts"


@lru_cache(maxsize=32)
def _load_template(name: str) -> str:
    """Load a raw template file. Cached after first access."""
    path = PROMPTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


def load_prompt(name: str, **variables: Any) -> str:
    """
    Load a prompt template and substitute variables.

    Args:
        name: Template filename (e.g., 'support_system.txt').
        **variables: Key-value pairs to substitute in the template.

    Returns:
        Rendered prompt string.
    """
    template = _load_template(name)

    for key, value in variables.items():
        placeholder = "{" + key + "}"
        template = template.replace(placeholder, str(value))

    return template


def get_support_system_prompt(
    *,
    context: str,
    history: str = "",
    question: str,
) -> str:
    """Load the support system prompt with context and question."""
    return load_prompt(
        "support_system.txt",
        context=context,
        history=history,
        question=question,
    )


def get_summary_prompt(*, conversation: str) -> str:
    """Load the conversation summary prompt."""
    return load_prompt(
        "conversation_summary.txt",
        conversation=conversation,
    )
