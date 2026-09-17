"""
Chat API Router.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.database.connection import get_db_session
from app.modules.chat.service import ChatService
from app.modules.rag.service import RAGService
from app.modules.llm.service import GenerationService
from app.modules.rag.retriever import SemanticRetriever
from app.modules.rag.confidence import ConfidenceEvaluator
from app.modules.rag.context_builder import ContextBuilder
from app.database.repositories.chunk import ChunkRepository
from app.modules.embeddings.providers.sentence_transformers import SentenceTransformersProvider
from app.modules.embeddings.service import EmbeddingService
from app.integrations.gemini.provider import GeminiLLMProvider
from app.core.config import get_settings

router = APIRouter(tags=["Chat"])

class ChatRequest(BaseModel):
    query: str

# Module-level singleton to avoid loading the ~100MB ML model into RAM on every request.
_emb_provider: SentenceTransformersProvider | None = None

def get_embedding_provider() -> SentenceTransformersProvider:
    global _emb_provider
    if _emb_provider is None:
        _emb_provider = SentenceTransformersProvider()
    return _emb_provider

# In a real DI setup (e.g. using FastAPI Depends or dependency-injector), 
# this would be much cleaner. For now, we wire it manually in the dependency.
async def get_chat_service(session=Depends(get_db_session)) -> ChatService:
    settings = get_settings()
    
    # Repos
    chunk_repo = ChunkRepository(session)
    
    # Services
    emb_provider = get_embedding_provider()
    emb_service = EmbeddingService(emb_provider, settings.embedding)
    retriever = SemanticRetriever(chunk_repo, emb_service)
    
    evaluator = ConfidenceEvaluator(settings.rag)
    context_builder = ContextBuilder(settings.rag)
    rag_service = RAGService(retriever, evaluator, context_builder, settings.rag)
    gemini_provider = GeminiLLMProvider(settings.gemini)
    gen_service = GenerationService(gemini_provider)
    
    return ChatService(rag_service, gen_service)


@router.post("")
async def chat_endpoint(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Ask a question to the AI Support Bot.
    """
    result = await chat_service.chat(request.query)
    return {
        "success": True,
        "data": result
    }
