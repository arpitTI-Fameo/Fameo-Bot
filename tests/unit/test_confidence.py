"""
Unit tests for confidence evaluator.
"""

from __future__ import annotations

from app.core.config import RAGSettings
from app.core.constants import ConfidenceLevel
from app.modules.rag.confidence import ConfidenceEvaluator


class TestConfidenceEvaluator:
    def setup_method(self):
        settings = RAGSettings(min_confidence=0.3)
        self.evaluator = ConfidenceEvaluator(settings)

    def test_no_scores_returns_none(self):
        result = self.evaluator.evaluate([])
        assert result.level == ConfidenceLevel.NONE
        assert result.should_generate is False
        assert result.score == 0.0

    def test_high_confidence(self):
        result = self.evaluator.evaluate([0.95, 0.90, 0.85])
        assert result.level == ConfidenceLevel.HIGH
        assert result.should_generate is True
        assert result.score > 0.7

    def test_medium_confidence(self):
        result = self.evaluator.evaluate([0.5, 0.45, 0.4])
        assert result.level == ConfidenceLevel.MEDIUM
        assert result.should_generate is True

    def test_low_confidence(self):
        result = self.evaluator.evaluate([0.35, 0.3, 0.25])
        assert result.should_generate is True
        assert result.level in (ConfidenceLevel.LOW, ConfidenceLevel.MEDIUM)

    def test_below_minimum(self):
        result = self.evaluator.evaluate([0.1, 0.05])
        assert result.level == ConfidenceLevel.NONE
        assert result.should_generate is False

    def test_rerank_scores_preferred(self):
        # Low similarity but high rerank should give high confidence
        result = self.evaluator.evaluate(
            similarity_scores=[0.3, 0.25],
            rerank_scores=[0.95, 0.90],
        )
        assert result.level == ConfidenceLevel.HIGH
        assert result.should_generate is True

    def test_single_score(self):
        result = self.evaluator.evaluate([0.8])
        assert result.level == ConfidenceLevel.HIGH
        assert result.should_generate is True
