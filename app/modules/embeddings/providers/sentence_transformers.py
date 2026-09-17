"""
Local Sentence Transformers embedding provider.
"""

from __future__ import annotations

import asyncio
from sentence_transformers import SentenceTransformer

from app.modules.embeddings.interfaces import EmbeddingProvider
from app.core.exceptions import EmbeddingError


class SentenceTransformersProvider(EmbeddingProvider):
    """
    Embedding provider using local SentenceTransformers models.
    Loads the model once in memory and runs embeddings.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._provider_name = "sentence-transformers"
        
        # Load the model synchronously on startup (or lazy load).
        # We wrap this in a try-except to catch missing dependencies gracefully.
        try:
            self._model = SentenceTransformer(model_name)
        except Exception as e:
            raise EmbeddingError(f"Failed to load sentence-transformers model {model_name}: {e}") from e

    @property
    def dimension(self) -> int:
        return self._model.get_sentence_embedding_dimension()

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def provider_name(self) -> str:
        return self._provider_name

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings using run_in_executor to avoid blocking the event loop.
        """
        if not texts:
            return []
            
        loop = asyncio.get_running_loop()
        try:
            # SentenceTransformer.encode returns a numpy array or tensor, 
            # we convert it to a python list of floats.
            embeddings = await loop.run_in_executor(
                None,
                lambda: self._model.encode(texts, convert_to_numpy=True)
            )
            return embeddings.tolist()
        except Exception as e:
            raise EmbeddingError(f"SentenceTransformers embedding failed: {e}") from e

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        results = await self.embed_documents([text])
        return results[0]
