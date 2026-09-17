# AI Support Bot Backend

A streamlined AI Support Backend with Retrieval-Augmented Generation (RAG) over document knowledge bases.

## Architecture

This project was recently simplified to focus purely on the core RAG and chat flow. Background workers, rate limiting, and conversational tracking have been stripped out for maximum clarity.

- **API**: FastAPI (async, stateless)
- **Database**: Supabase PostgreSQL + `pgvector`
- **LLM**: Gemini (via `google-genai` SDK)
- **Embeddings**: Sentence Transformers (runs locally to avoid API latency)

### The Flow
1. **Query:** User sends a query to the `/chat` endpoint.
2. **Embed:** The `sentence-transformers` model (cached in memory on startup) converts the query into a vector.
3. **Retrieve:** The RAG module runs a similarity search against the Supabase `pgvector` database to find the most relevant document chunks.
4. **Generate:** The chunks and query are sent to the Gemini API, which generates a grounded response.

## Quick Start

### Prerequisites
- Python 3.12+
- Supabase project (PostgreSQL)

### Setup

```bash
# Clone and enter
cd support_ai.egg-info

# Create .env from template
cp .env.example .env
# Edit .env with your credentials

# Install dependencies
pip install -e ".[dev]"

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Liveness probe |
| GET | `/api/v1/ready` | Readiness probe (checks DB) |
| POST | `/api/v1/chat` | Chat with RAG |

## Project Structure

```
support-ai/
├── app/                   # Application code
│   ├── api/               # HTTP layer (routers, schemas, dependencies)
│   ├── core/              # Cross-cutting (config, logging, security, middleware)
│   ├── database/          # Models, repositories, connection
│   ├── modules/           # Domain logic (chat, rag, llm, embeddings)
│   ├── integrations/      # External providers (Gemini)
│   └── prompts/           # LLM prompt templates
├── alembic/               # Database migrations
├── scripts/               # Operational scripts (e.g. test_chat.py)
```
