"""
Local Chat Tester Script
"""

import asyncio
from app.core.config import get_settings
from app.database.connection import init_database, get_session
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

async def test_chat():
    settings = get_settings()
    print("Init database...")
    init_database(settings.database)
    
    query = "How do I cancel my subscription and get a refund?"
    print(f"Testing Chat with query: '{query}'")
    
    print("Opening DB session...")
    async with get_session() as session:
        print("Initializing services...")
        chunk_repo = ChunkRepository(session)
        emb_provider = SentenceTransformersProvider()
        emb_service = EmbeddingService(emb_provider, settings.embedding)
        retriever = SemanticRetriever(chunk_repo, emb_service)
        
        evaluator = ConfidenceEvaluator(settings.rag)
        settings.rag.context_token_limit = 1000
        settings.gemini.max_tokens = 512
        context_builder = ContextBuilder(settings.rag)
        rag_service = RAGService(retriever, evaluator, context_builder, settings.rag)
        
        gemini_provider = GeminiLLMProvider(settings.gemini)
        gen_service = GenerationService(gemini_provider)
        
        chat_service = ChatService(rag_service, gen_service)
        
        print("Calling chat_service.chat()...")
        try:
            result = await chat_service.chat(query)
            print("====== RESULT ======")
            print("Answer:", result["answer"])
            print("Confidence:", result["confidence"])
            print("Sources:", len(result["sources"]))
        except Exception as e:
            print(f"Exception during chat: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat())
