# ChatDock Architecture

## Backend
- FastAPI app organized by `api/routes`, `schemas`, `services`, `core`, and `rag`.
- Auth, bot management, document upload/chunking, chat, and analytics endpoints.
- Optional external integrations:
- PostgreSQL via SQLAlchemy (`app/database/connection.py`, `app/database/models.py`)
- Redis for cache and rate limiting (`app/core/cache.py`, `app/core/rate_limiter.py`)
- Qdrant for vector search (`app/rag/vector_store.py`)
- OpenAI for embeddings and response generation (`app/rag/embeddings.py`, `app/services/chat_service.py`)

## Async Workers
- Celery worker app and task scaffold in `app/workers`.
- Redis-backed broker/result backend by default.

## Infrastructure
- `infrastructure/docker-compose.yml` provisions Postgres, Redis, Qdrant, backend API, and worker.

## Database Migrations
- Alembic is configured via `backend/alembic.ini`.
- Migration scripts live in `backend/app/database/migrations/versions`.
- Apply migrations with:
- `cd backend`
- `python -m alembic upgrade head`
