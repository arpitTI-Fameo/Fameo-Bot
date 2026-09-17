"""
Generation service.
"""

from __future__ import annotations

from app.modules.llm.interfaces import LLMProvider, LLMMessage, LLMResponse
from app.modules.llm.prompts.loader import load_prompt


class GenerationService:
    def __init__(self, provider: LLMProvider):
        self._provider = provider

    async def generate_support_response(
        self,
        query: str,
        context: str,
        history: list[dict[str, str]] | None = None
    ) -> LLMResponse:
        """
        Generate a response for a user query using the provided RAG context.
        """
        system_prompt = load_prompt("support_system.txt", context=context, question=query)
        
        messages = [LLMMessage(role="system", content=system_prompt)]
        
        if history:
            for msg in history:
                messages.append(LLMMessage(role=msg["role"], content=msg["content"]))
            
        messages.append(LLMMessage(role="user", content=query))
        
        return await self._provider.generate(
            messages=messages,
            temperature=0.1,  # low temp for support
            max_tokens=2048,
        )
