"""
LLM provider interfaces — protocol-based abstraction.

Any LLM backend (Groq, OpenAI, Anthropic, etc.) implements this protocol.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class LLMMessage:
    """A single message in an LLM conversation."""
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    provider: str = ""
    latency_ms: int = 0
    metadata: dict = field(default_factory=dict)


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    @property
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'groq', 'openai')."""
        ...

    @property
    def model_name(self) -> str:
        """Return the model identifier."""
        ...

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        """
        Generate a completion from the LLM.

        Args:
            messages: Conversation messages.
            max_tokens: Max tokens to generate.
            temperature: Sampling temperature.
            stop: Stop sequences.

        Returns:
            LLMResponse with content and usage metadata.
        """
        ...
