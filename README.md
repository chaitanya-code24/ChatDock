# ChatDock

ChatDock is an AI SaaS starter platform for building document-trained chatbots.

Users can:
- register/login
- create and manage bots
- upload documents (`.pdf`, `.txt`, `.docx`, `.md`)
- chat with bots using a RAG pipeline
- view basic analytics
- integrate bots via widget snippet or API request

## Tech Stack

- Frontend: Next.js 16 + Tailwind CSS
- Backend: FastAPI (Python)
- Database: PostgreSQL (SQLAlchemy)
- Vector Search: Qdrant
- Cache + Rate Limiting: Redis
- Worker: Celery
- LLM: Groq/OpenAI-compatible client (configurable)

## Repository Structure

```text
backend/         FastAPI app, RAG pipeline, DB models, services
frontend/        Next.js dashboard and bot management UI
infrastructure/  Docker Compose for local stack
docs/            Architecture and API docs
scripts/         Setup and local utility scripts
widget/          Widget-related JS/CSS assets
```

## Quick Start (Docker)

1. Configure backend environment:

```bash
cp backend/.env.example backend/.env
```

If `.env.example` is unavailable, create `backend/.env` manually using the required keys from `backend/app/core/config.py`.

2. Start services:

```bash
docker compose -f infrastructure/docker-compose.yml up -d --build
```

3. Run frontend:

```bash
cd frontend
npm install
npm run dev
```

4. Open:
- Frontend: `http://localhost:3000` (or next available port)
- Backend health: `http://localhost:8000/health`

## Core API Endpoints

- `POST /auth/register`
- `POST /auth/login`
- `POST /bot/create`
- `GET /bot/list`
- `DELETE /bot/{bot_id}`
- `POST /bot/upload?bot_id=...`
- `POST /chat`
- `GET /analytics/overview`

## Product Flow

1. Create account and login
2. Create a bot from Dashboard
3. Open Manage Bot
4. Upload documents
5. Test in Chat Interface
6. Use Integrations section for widget/API snippets

## Notes

- Cache and rate limiting are enabled with Redis.
- RAG quality depends on document quality and uploaded content coverage.
- Keep secrets out of Git (`.env` is ignored).

## Status

MVP is functional and demo-ready:
- auth
- bot lifecycle
- document ingestion
- RAG chat
- integrations UI

---

For deeper details, see:
- `docs/architecture.md`
- `docs/api_docs.md`
