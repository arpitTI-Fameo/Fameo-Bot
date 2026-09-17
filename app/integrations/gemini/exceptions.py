"""
Gemini-specific exceptions.

Maps google-generativeai exceptions to our internal LLMError hierarchy.
"""

from app.core.exceptions import (
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
)

class GeminiAPIError(LLMError):
    """Generic Gemini API error."""
    error_code = "GEMINI_API_ERROR"

class GeminiAuthenticationError(GeminiAPIError):
    """Invalid API key or authentication failure."""
    error_code = "GEMINI_AUTH_ERROR"

class GeminiModelNotFoundError(GeminiAPIError):
    """The requested model does not exist or you don't have access to it."""
    error_code = "GEMINI_MODEL_NOT_FOUND"

class GeminiRateLimitError(LLMRateLimitError):
    """Gemini rate limit hit."""
    error_code = "GEMINI_RATE_LIMITED"

class GeminiTimeoutError(LLMTimeoutError):
    """Gemini request timed out."""
    error_code = "GEMINI_TIMEOUT"
