# ChatDock

<p align="center">
  <img src="https://img.shields.io/badge/ChatDock-RAG%20SaaS-7c3aed?style=for-the-badge" alt="ChatDock"/>
  <img src="https://img.shields.io/badge/Status-MVP%20Ready-16a34a?style=for-the-badge" alt="MVP Ready"/>
</p>

<p align="center">
  <b>Launch document-trained chatbots in minutes.</b><br/>
  Upload files • train context • test responses • embed anywhere
</p>

<p align="center">
  <img alt="Backend" src="https://img.shields.io/badge/Backend-FastAPI-0ea5e9?style=flat-square"/>
  <img alt="Frontend" src="https://img.shields.io/badge/Frontend-Next.js-111827?style=flat-square"/>
  <img alt="Database" src="https://img.shields.io/badge/PostgreSQL-Data%20Layer-2563eb?style=flat-square"/>
  <img alt="Vector DB" src="https://img.shields.io/badge/Qdrant-Vector%20Search-7c3aed?style=flat-square"/>
  <img alt="Cache" src="https://img.shields.io/badge/Redis-Cache%20%2B%20RateLimit-dc2626?style=flat-square"/>
  <img alt="LLM" src="https://img.shields.io/badge/LLM-Groq%20%7C%20OpenAI-0f766e?style=flat-square"/>
</p>

## Overview

ChatDock is an AI platform starter that helps teams build and deploy document-aware chatbots.  
It provides authentication, bot lifecycle management, file ingestion, RAG chat, and integration snippets in one workflow.

### Why It Feels Product-Ready

- Workspace with multiple bots per account
- Instant doc-to-chat pipeline (`.pdf`, `.txt`, `.docx`, `.md`)
- Retrieval-augmented answers with context grounding
- API and widget integration out of the box
- Redis-powered caching + rate limiting
- Built-in usage and content analytics

## Product Workflow

```text
Create Bot -> Upload Docs -> Chat Test -> Integrate -> Launch
```

1. Register / login
2. Create bot from Dashboard
3. Open `Manage Bot`
4. Upload documents
5. Validate in `Chat Interface`
6. Publish using `Integrations` snippets

## Feature Matrix

| Area | Included in MVP |
|---|---|
| Authentication | Register/Login with token session |
| Bot Management | Create/List/Delete |
| Document Pipeline | Upload -> Parse -> Chunk -> Index |
| RAG Chat | Context retrieval + LLM answer |
| Caching | Redis response cache |
| API Protection | Redis-based rate limiting |
| Integrations | Widget script + API request templates |
| Analytics | Bot/doc/chunk/query overview |

## Architecture

```text
Next.js Dashboard
      |
      v
FastAPI API Layer
  |- Auth/Bot/Doc/Chat routes
  |- RAG services
  |
  +--> PostgreSQL (users, bots, docs, chunks, logs)
  +--> Qdrant (vector retrieval)
  +--> Redis (cache + rate limit)
  +--> LLM Provider (Groq/OpenAI-compatible)
```

## Tech Stack

- **Frontend:** Next.js 16, Tailwind CSS
- **Backend:** FastAPI, Python
- **ORM:** SQLAlchemy
- **Primary DB:** PostgreSQL
- **Vector DB:** Qdrant
- **Cache + Rate Limit:** Redis
- **Worker:** Celery
- **LLM Layer:** Configurable provider (Groq/OpenAI-compatible)

## Repository Layout

```text
backend/         FastAPI app, RAG pipeline, DB models, services
frontend/        Dashboard and bot management UI
infrastructure/  Docker Compose stack
docs/            Architecture and API docs
scripts/         Local setup helpers
widget/          Widget assets
```

## Quick Start

### Fastest Local Boot

```bash
docker compose -f infrastructure/docker-compose.yml up -d --build
cd frontend && npm install && npm run dev
```

### 1) Configure environment

Create `backend/.env` using keys referenced in:
- `backend/app/core/config.py`

### 2) Start backend stack

```bash
docker compose -f infrastructure/docker-compose.yml up -d --build
```

### 3) Start frontend

```bash
cd frontend
npm install
npm run dev
```

### 4) Access

- App: `http://localhost:3000` (or next free port)
- API health: `http://localhost:8000/health`

## API (MVP)

- `POST /auth/register`
- `POST /auth/login`
- `POST /bot/create`
- `GET /bot/list`
- `DELETE /bot/{bot_id}`
- `POST /bot/upload?bot_id=...`
- `POST /chat`
- `GET /analytics/overview`

## Launch Checklist

- [ ] Add production `.env` secrets
- [ ] Rotate any exposed API keys
- [ ] Validate retrieval quality on real client docs
- [ ] Enable monitoring and alerting
- [ ] Configure backups for PostgreSQL and Qdrant

## Documentation

- Architecture: `docs/architecture.md`
- API docs: `docs/api_docs.md`

---

<p align="center">
  <b>ChatDock</b> • Build once, deploy everywhere
</p>
