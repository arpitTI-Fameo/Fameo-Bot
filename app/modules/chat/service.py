"""
Chat Service.
Combines RAG retrieval and LLM generation.
"""

from __future__ import annotations

from typing import Any

from app.modules.rag.service import RAGService
from app.modules.llm.service import GenerationService


class ChatService:
    def __init__(self, rag_service: RAGService, gen_service: GenerationService):
        self._rag_service = rag_service
        self._gen_service = gen_service

    async def chat(self, query: str) -> dict[str, Any]:
        """
        Process a user query, perform RAG, and return the final answer.
        """
        # 1. Get Context
        context_str, sources, confidence = await self._rag_service.get_context_for_query(query)
        
        # 2. Check confidence (if too low, we might fallback, but for now we just pass it)
        if confidence.level == "LOW" or not sources:
            return {
                "answer": "I'm sorry, I couldn't find any information in the knowledge base to answer your question.",
                "sources": [],
                "confidence": {"level": "LOW", "score": 0.0}
            }

        # 3. Generate Answer
        response = await self._gen_service.generate_support_response(
            query=query,
            context=context_str
        )
        
        # 4. Format Sources
        formatted_sources = []
        for src in sources:
            formatted_sources.append({
                "source_id": src.chunk_id,
                "score": src.relevance_score,
                "metadata": {
                    "document_name": src.document_name,
                    "page": src.page,
                    "section": src.section
                }
            })
            
        return {
            "answer": response.content,
            "sources": formatted_sources,
            "confidence": {
                "level": confidence.level.name,
                "score": confidence.score
            },
            "usage": {
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "total_tokens": response.total_tokens
            }
        }
