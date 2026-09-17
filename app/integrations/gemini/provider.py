"""
Gemini LLM provider — implements the LLMProvider protocol.

This is the ONLY place Gemini SDK/API calls should exist in the codebase.
"""

from __future__ import annotations

import time
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.core.config import GeminiSettings
from app.core.logging import get_logger
from app.core.telemetry import LLM_LATENCY, LLM_REQUEST_COUNT, LLM_TOKENS
from app.integrations.gemini.exceptions import (
    GeminiAPIError,
    GeminiAuthenticationError,
    GeminiModelNotFoundError,
    GeminiRateLimitError,
    GeminiTimeoutError,
)
from app.modules.llm.interfaces import LLMMessage, LLMResponse

logger = get_logger(__name__)


class GeminiLLMProvider:
    """
    LLMProvider implementation for Gemini.

    Satisfies the LLMProvider protocol via duck typing.
    """

    def __init__(self, settings: GeminiSettings) -> None:
        self._settings = settings
        self._client = genai.Client(api_key=settings.api_key.get_secret_value())

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._settings.model

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        """Generate a completion via Gemini API."""
        contents = []
        system_instruction = None

        for m in messages:
            if m.role == "system":
                if system_instruction is None:
                    system_instruction = m.content
                else:
                    system_instruction += "\n" + m.content
            else:
                role = "user" if m.role == "user" else "model"
                contents.append(
                    types.Content(role=role, parts=[types.Part.from_text(text=m.content)])
                )

        config_kwargs = {
            "max_output_tokens": max_tokens or self._settings.max_tokens,
            "temperature": temperature if temperature is not None else self._settings.temperature,
            "stop_sequences": stop,
        }
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
            
        config = types.GenerateContentConfig(**config_kwargs)

        start = time.perf_counter()
        
        last_error: Exception | None = None
        for attempt in range(1, self._settings.max_retries + 1):
            try:
                response = await self._client.aio.models.generate_content(
                    model=self._settings.model,
                    contents=contents,
                    config=config,
                )
                
                elapsed_ms = int((time.perf_counter() - start) * 1000)

                prompt_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
                completion_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else 0
                total_tokens = response.usage_metadata.total_token_count if response.usage_metadata else 0
                
                content = response.text or ""

                # Record metrics
                LLM_REQUEST_COUNT.labels(
                    provider="gemini", model=self._settings.model, status="success"
                ).inc()
                LLM_LATENCY.labels(
                    provider="gemini", model=self._settings.model
                ).observe(elapsed_ms / 1000)
                LLM_TOKENS.labels(
                    provider="gemini", model=self._settings.model, token_type="prompt"
                ).inc(prompt_tokens)
                LLM_TOKENS.labels(
                    provider="gemini", model=self._settings.model, token_type="completion"
                ).inc(completion_tokens)

                logger.info(
                    "llm_generation_complete",
                    provider="gemini",
                    model=self._settings.model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    latency_ms=elapsed_ms,
                )

                return LLMResponse(
                    content=content,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    model=self._settings.model,
                    provider="gemini",
                    latency_ms=elapsed_ms,
                )

            except APIError as e:
                if e.code == 429:
                    logger.warning("gemini_rate_limited", attempt=attempt)
                    last_error = GeminiRateLimitError(f"Rate limited: {e.message}")
                    await self._backoff(attempt)
                elif e.code in (503, 504):
                    logger.warning("gemini_timeout", attempt=attempt)
                    last_error = GeminiTimeoutError(f"Service unavailable or timed out: {e.message}")
                    await self._backoff(attempt)
                elif e.code in (401, 403):
                    raise GeminiAuthenticationError(f"Authentication failed: {e.message}")
                elif e.code == 404:
                    raise GeminiModelNotFoundError(f"Model not found: {e.message}")
                else:
                    logger.error("gemini_api_error", error=str(e), attempt=attempt)
                    last_error = GeminiAPIError(f"API error: {e.message}")
                    await self._backoff(attempt)
            except Exception as e:
                logger.error("gemini_api_error", error=str(e), attempt=attempt)
                last_error = GeminiAPIError(f"API error: {e}")
                await self._backoff(attempt)

        raise last_error or GeminiAPIError("All retry attempts exhausted")

    async def _backoff(self, attempt: int) -> None:
        """Exponential backoff with jitter."""
        import asyncio
        import random
        delay = min(2 ** attempt + random.uniform(0, 1), 30)
        logger.info("gemini_retry_backoff", attempt=attempt, delay_s=round(delay, 2))
        await asyncio.sleep(delay)

    async def close(self) -> None:
        """Clean up resources. genai library handles connections internally."""
        pass
