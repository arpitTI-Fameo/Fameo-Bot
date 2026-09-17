# AI Support Bot Backend

Production-grade AI Support Backend with RAG over PDF/document knowledge bases.

## Architecture

- **API**: FastAPI (async, stateless, horizontally scalable)
- **Database**: Supabase PostgreSQL + pgvector
- **Cache/Broker**: Redis
- **Workers**: Celery (async document ingestion)
- **LLM**: Gemini SDK (behind provider abstraction)
- **Embeddings**: Sentence Transformers (swappable via config)

## Quick Start

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- Supabase project (PostgreSQL + Storage)
- Redis

### Setup

```bash
# Clone and enter
cd support-ai

# Create .env from template
cp .env.example .env
# Edit .env with your credentials

# Install dependencies
pip install -e ".[dev]"

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Build and run all services
docker compose up --build

# Run API only
docker compose up support-api

# Run worker only
docker compose up support-worker
```

### Testing

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/ -v

# With coverage
pytest --cov=app --cov-report=html
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Liveness probe |
| GET | `/api/v1/ready` | Readiness probe |
| POST | `/api/v1/chat` | Chat with RAG |
| POST | `/api/v1/conversations` | Create conversation |
| GET | `/api/v1/conversations` | List conversations |
| POST | `/api/v1/documents` | Upload document |
| POST | `/api/v1/ingestion/jobs` | Trigger ingestion |
| POST | `/api/v1/feedback` | Submit feedback |

## Project Structure

```
support-ai/
├── app/                   # Application code
│   ├── api/               # HTTP layer (routers, schemas, dependencies)
│   ├── core/              # Cross-cutting (config, logging, security, middleware)
│   ├── database/          # Models, repositories, connection
│   ├── modules/           # Domain logic (chat, rag, documents, llm, etc.)
│   ├── integrations/      # External providers (Gemini, Supabase, Redis)
│   ├── workers/           # Celery tasks
│   └── prompts/           # LLM prompt templates
├── alembic/               # Database migrations
├── tests/                 # Test suite
├── scripts/               # Operational scripts
└── docs/                  # Documentation
```

## Documentation

- [Architecture](docs/architecture.md)
- [API Reference](docs/api.md)
- [RAG Pipeline](docs/rag.md)
- [Deployment](docs/deployment.md)
- [Operations](docs/operations.md)
