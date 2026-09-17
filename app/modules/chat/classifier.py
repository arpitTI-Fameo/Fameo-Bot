"""
Query classification.

Classifies incoming user queries to route them through the appropriate
response pathway (RAG, general support, out of scope, etc.).
"""

from __future__ import annotations

import re
from typing import Any

from app.core.constants import QueryCategory
from app.core.logging import get_logger

logger = get_logger(__name__)

# Patterns indicating account-specific queries
_ACCOUNT_PATTERNS = re.compile(
    r"\b(my account|my order|my subscription|my billing|my invoice|"
    r"my payment|my profile|my plan|my balance|order #|order number|"
    r"tracking|refund status|account balance|cancel my)\b",
    re.IGNORECASE,
)

# Patterns indicating out-of-scope queries
_OUT_OF_SCOPE_PATTERNS = re.compile(
    r"\b(what is the weather|tell me a joke|write a poem|"
    r"write code|translate|who is the president|"
    r"ignore previous|forget your instructions|"
    r"you are now|act as|pretend to be|system prompt|"
    r"reveal your|what are your instructions)\b",
    re.IGNORECASE,
)

# Greetings / general support
_GENERAL_PATTERNS = re.compile(
    r"^(hi|hello|hey|thanks|thank you|bye|goodbye|help|"
    r"how can you help|what can you do|who are you)\b",
    re.IGNORECASE,
)


class QueryClassifier:
    """
    Lightweight rule-based query classifier.

    Categories:
    - KNOWLEDGE_QUERY → RAG pipeline
    - GENERAL_SUPPORT → controlled generic response
    - OUT_OF_SCOPE   → safe refusal
    - ACCOUNT_SPECIFIC → future tool, explicit fallback now
    - UNKNOWN         → safe fallback
    """

    def classify(self, query: str) -> QueryCategory:
        """Classify a user query into a category."""
        query_stripped = query.strip()

        if not query_stripped:
            return QueryCategory.UNKNOWN

        # Check for prompt injection / out of scope first (safety)
        if _OUT_OF_SCOPE_PATTERNS.search(query_stripped):
            logger.info("query_classified", category="out_of_scope", query_len=len(query_stripped))
            return QueryCategory.OUT_OF_SCOPE

        # Check for account-specific queries
        if _ACCOUNT_PATTERNS.search(query_stripped):
            logger.info("query_classified", category="account_specific", query_len=len(query_stripped))
            return QueryCategory.ACCOUNT_SPECIFIC

        # Check for greetings / general
        if _GENERAL_PATTERNS.match(query_stripped):
            logger.info("query_classified", category="general_support", query_len=len(query_stripped))
            return QueryCategory.GENERAL_SUPPORT

        # Default: knowledge query → RAG
        logger.info("query_classified", category="knowledge_query", query_len=len(query_stripped))
        return QueryCategory.KNOWLEDGE_QUERY


# Pre-built responses for non-RAG categories
CATEGORY_RESPONSES = {
    QueryCategory.GENERAL_SUPPORT: (
        "Hello! I'm your AI support assistant. I can help answer questions "
        "based on our documentation and knowledge base. How can I assist you today?"
    ),
    QueryCategory.OUT_OF_SCOPE: (
        "I'm a support assistant and can only help with questions related to "
        "our products and services. I'm not able to help with that request."
    ),
    QueryCategory.ACCOUNT_SPECIFIC: (
        "I understand you have an account-specific question. Currently, I can only "
        "answer general questions from our documentation. For account-specific inquiries, "
        "please contact our support team directly or use your account dashboard."
    ),
    QueryCategory.UNKNOWN: (
        "I'm not sure I understand your question. Could you please rephrase it? "
        "I can help with questions about our products, services, and policies."
    ),
}
