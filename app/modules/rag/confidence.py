"""
RAG confidence scoring.

Evaluates retrieval quality to decide whether to generate
an authoritative answer or return a controlled fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import RAGSettings
from app.core.constants import ConfidenceLevel
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ConfidenceResult:
    """Result of confidence evaluation."""
    level: ConfidenceLevel
    score: float
    reason: str
    should_generate: bool


class ConfidenceEvaluator:
    """
    Evaluates retrieval confidence based on configurable thresholds.

    Thresholds:
    - HIGH:   score >= 0.7  → generate authoritative answer
    - MEDIUM: score >= 0.4  → generate with disclaimer
    - LOW:    score >= min   → generate with strong disclaimer
    - NONE:   score < min   → fallback, no generation
    """

    HIGH_THRESHOLD = 0.7
    MEDIUM_THRESHOLD = 0.4

    def __init__(self, settings: RAGSettings) -> None:
        self._min_confidence = settings.min_confidence

    def evaluate(
        self,
        similarity_scores: list[float],
        *,
        rerank_scores: list[float] | None = None,
    ) -> ConfidenceResult:
        """
        Evaluate confidence from retrieval scores.

        Uses the best score from reranking if available, else similarity.
        """
        if not similarity_scores:
            return ConfidenceResult(
                level=ConfidenceLevel.NONE,
                score=0.0,
                reason="No documents retrieved",
                should_generate=False,
            )

        # Use rerank scores if available, else similarity
        scores = rerank_scores if rerank_scores else similarity_scores

        # Aggregate: max score weighted with top-3 average
        top_score = max(scores)
        top_3_avg = sum(sorted(scores, reverse=True)[:3]) / min(len(scores), 3)
        composite = 0.6 * top_score + 0.4 * top_3_avg

        if composite >= self.HIGH_THRESHOLD:
            return ConfidenceResult(
                level=ConfidenceLevel.HIGH,
                score=composite,
                reason="Strong retrieval match",
                should_generate=True,
            )
        elif composite >= self.MEDIUM_THRESHOLD:
            return ConfidenceResult(
                level=ConfidenceLevel.MEDIUM,
                score=composite,
                reason="Moderate retrieval match",
                should_generate=True,
            )
        elif composite >= self._min_confidence:
            return ConfidenceResult(
                level=ConfidenceLevel.LOW,
                score=composite,
                reason="Weak retrieval match — answer may be incomplete",
                should_generate=True,
            )
        else:
            return ConfidenceResult(
                level=ConfidenceLevel.NONE,
                score=composite,
                reason="Insufficient retrieval confidence",
                should_generate=False,
            )
