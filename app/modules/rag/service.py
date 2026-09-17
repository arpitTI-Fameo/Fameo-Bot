"""
RAG Service Facade.
Orchestrates retrieval, confidence evaluation, and context building.
"""

from __future__ import annotations

from typing import Any

from app.modules.rag.retriever import SemanticRetriever
from app.modules.rag.confidence import ConfidenceEvaluator, ConfidenceResult
from app.modules.rag.context_builder import ContextBuilder, ContextSource
from app.core.config import RAGSettings


class RAGService:
    def __init__(
        self,
        retriever: SemanticRetriever,
        evaluator: ConfidenceEvaluator,
        context_builder: ContextBuilder,
        settings: RAGSettings,
    ):
        self._retriever = retriever
        self._evaluator = evaluator
        self._context_builder = context_builder
        self._settings = settings

    async def get_context_for_query(
        self, query: str
    ) -> tuple[str, list[ContextSource], ConfidenceResult]:
        """
        Retrieve chunks, evaluate confidence, and build the context string.
        """
        # 1. Retrieve
        raw_results = await self._retriever.retrieve(
            query=query,
            top_k=self._settings.top_k,
        )
        
        # 2. Evaluate Confidence
        scores = [row["similarity_score"] for row in raw_results]
        confidence = self._evaluator.evaluate(scores)
        
        # 3. Build Context String and Sources
        # We need to map similarity_score to relevance_score for ContextBuilder
        for row in raw_results:
            row["relevance_score"] = row["similarity_score"]
            row["document_name"] = "Knowledge Base Document" # We should join with document table for real name later
            
        built_context = self._context_builder.build(raw_results)
        
        return built_context.text, built_context.sources, confidence
