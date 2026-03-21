# ChatDock

<p align="center">
  <img src="https://img.shields.io/badge/ChatDock-Document%20QA%20Platform-2459ea?style=for-the-badge" alt="ChatDock"/>
  <img src="https://img.shields.io/badge/Status-Active%20Project-0f766e?style=for-the-badge" alt="Active Project"/>
</p>

<p align="center">
  Build document-aware chatbots with FastAPI, Next.js, PostgreSQL, Redis, and Qdrant.
</p>

<p align="center">
  <img alt="Backend" src="https://img.shields.io/badge/Backend-FastAPI-0ea5e9?style=flat-square"/>
  <img alt="Frontend" src="https://img.shields.io/badge/Frontend-Next.js-111827?style=flat-square"/>
  <img alt="Database" src="https://img.shields.io/badge/PostgreSQL-Persistence-2563eb?style=flat-square"/>
  <img alt="Vector DB" src="https://img.shields.io/badge/Qdrant-Vector%20Search-7c3aed?style=flat-square"/>
  <img alt="Cache" src="https://img.shields.io/badge/Redis-Cache%20%2B%20Rate%20Limit-dc2626?style=flat-square"/>
  <img alt="LLM" src="https://img.shields.io/badge/LLM-Groq%20%7C%20OpenAI%20Compatible-0f766e?style=flat-square"/>
</p>

## Overview

ChatDock is a full-stack project for building and testing document-trained chatbots.

It includes:
- account auth
- multi-bot workspace management
- structured document ingestion
- hybrid RAG retrieval
- persistent chat threads
- widget and API integration
- usage analytics

The project is designed as a practical document-QA platform, not a generic chatbot shell.

## Current Product Flow

```text
Register/Login
  -> Create Bot
  -> Upload Documents
  -> Test in Chat
  -> Tune Bot Settings
  -> Use Widget/API
  -> Review Analytics
```

## Current Architecture

```text
Next.js Frontend
  |- Landing page
  |- Auth pages
  |- Dashboard
  |- Bot management
  |- Chat interface
  |- Integrations
  |- Analytics
  |
  v
FastAPI Backend
  |- auth routes
  |- bot routes
  |- document routes
  |- chat routes
  |- analytics routes
  |
  |- bot service
  |- document service
  |- chat service
  |- RAG modules
  |
  +--> PostgreSQL
  +--> Redis
  +--> Qdrant
  +--> LLM provider
```

## Backend Architecture

The backend is organized under `backend/app`:

```text
api/
  routes/
core/
database/
models/
schemas/
services/
rag/
utils/
workers/
```

Main responsibilities:
- `api/routes`: HTTP endpoints
- `services`: business logic
- `database`: SQLAlchemy models + connection/runtime schema setup
- `rag`: ingestion, chunking, retrieval, reranking
- `core`: config, cache, rate limiting, conversation memory

## Current RAG Pipeline

### Ingestion

Current ingestion flow:

```text
Document upload
  -> parse_document()
  -> build_structured_chunks()
  -> section-preserving chunk storage
  -> embeddings
  -> Qdrant upsert
```

What happens during ingestion:
- raw text is extracted from PDF, DOCX, TXT, or MD
- structured chunks are created by the document processor
- sections carry metadata such as:
  - heading
  - normalized heading
  - section id
  - topic
  - type
- fallback raw chunking is used if structured chunking yields nothing
- embeddings are generated from chunk content and synced to Qdrant

Relevant files:
- [document_service.py](backend/app/services/document_service.py)
- [document_processor.py](backend/app/rag/document_processor.py)
- [chunking.py](backend/app/rag/chunking.py)
- [embeddings.py](backend/app/rag/embeddings.py)
- [vector_store.py](backend/app/rag/vector_store.py)

### Retrieval

Current retrieval flow:

```text
User query
  -> normalize query
  -> strict heading match
  -> if matched: return full section(s)
  -> else BM25 retrieval + vector retrieval
  -> merge candidates
  -> model-assisted rerank
  -> group by section_id
  -> select top sections
  -> assemble context
  -> LLM answer
  -> cache result
```

Key behavior:
- heading-first retrieval for deterministic exact-section lookup
- BM25 retrieval for lexical recall
- vector retrieval for semantic recall
- reranking on merged candidates
- grouping by `section_id` instead of loose chunk-only ranking
- full section context assembly before answer generation

Relevant files:
- [chat_service.py](backend/app/services/chat_service.py)
- [keyword_search.py](backend/app/rag/keyword_search.py)
- [query_rewriter.py](backend/app/rag/query_rewriter.py)
- [hybrid_ranker.py](backend/app/rag/hybrid_ranker.py)
- [reranker.py](backend/app/rag/reranker.py)
- [context_validator.py](backend/app/rag/context_validator.py)

## Chat System

The chat layer supports:
- conversation memory
- persistent chat threads
- rename/delete thread actions
- thread analytics logging
- response caching

Current behavior:
- each chat has a `conversation_id`
- chat threads are stored in backend persistence
- chat history is reused during follow-up answers
- cache is keyed with query + selected sections

Relevant files:
- [chat_service.py](backend/app/services/chat_service.py)
- [chat.py](backend/app/api/routes/chat.py)
- [chat_schema.py](backend/app/schemas/chat_schema.py)

## Bot Management

Bots support:
- create
- update
- archive/unarchive
- reindex
- delete

Bot settings currently stored and exposed:
- bot name
- description
- tone
- answer length
- fallback behavior
- system prompt
- greeting message

Relevant files:
- [bot.py](backend/app/api/routes/bot.py)
- [bot_service.py](backend/app/services/bot_service.py)
- [bot_schema.py](backend/app/schemas/bot_schema.py)

## Analytics

Current analytics support:
- total bots
- total documents
- total chunks
- total queries
- cache hit rate
- query trend over 7 days
- top queries
- bot-specific analytics scope

The frontend supports:
- overall analytics
- per-bot analytics filtering
- usage / performance / insights tabs

Relevant files:
- [chat_service.py](backend/app/services/chat_service.py)
- [page.tsx](frontend/src/app/dashboard/analytics/page.tsx)
- [analytics-client.tsx](frontend/src/app/dashboard/analytics/analytics-client.tsx)

## Integrations

ChatDock currently provides:
- API chat usage through backend endpoints
- embeddable widget script
- in-app widget preview

Integration layer includes:
- real `widget.js`
- live preview in frontend
- conversation continuity in widget
- shared backend `/chat` API

Relevant files:
- [widget.js](frontend/public/widget.js)
- [page.tsx](frontend/src/app/dashboard/bots/page.tsx)

## Persistence Layer

Primary persistence:
- PostgreSQL for users, bots, documents, chunks, chat logs, and chat threads
- Redis for cache + rate limit
- Qdrant for vector storage

There is also an in-memory fallback store for environments where database services are unavailable.

Relevant files:
- [connection.py](backend/app/database/connection.py)
- [models.py](backend/app/database/models.py)

## Tech Stack

- Frontend: Next.js 16, React, Tailwind CSS
- Backend: FastAPI, Python
- ORM: SQLAlchemy
- Database: PostgreSQL
- Cache: Redis
- Vector DB: Qdrant
- Worker scaffold: Celery
- LLM provider: Groq / OpenAI-compatible client

## Repository Layout

```text
backend/
  app/
frontend/
  src/
  public/
infrastructure/
docs/
scripts/
widget/
```

## Quick Start

### 1. Backend environment

Set values in:
- `backend/.env`

Core config is defined in:
- `backend/app/core/config.py`

### 2. Start infrastructure + backend

```bash
docker compose -f infrastructure/docker-compose.yml up -d --build
```

### 3. Start frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Open locally

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Health: `http://localhost:8000/health`

## Important API Routes

### Auth
- `POST /auth/register`
- `POST /auth/login`

### Bots
- `POST /bot/create`
- `GET /bot/list`
- `GET /bot/{bot_id}`
- `PATCH /bot/{bot_id}`
- `POST /bot/{bot_id}/archive`
- `POST /bot/{bot_id}/reindex`
- `DELETE /bot/{bot_id}`

### Documents
- `POST /bot/upload?bot_id=...`
- `GET /bot/documents?bot_id=...`
- `DELETE /bot/document/{document_id}?bot_id=...`

### Chat
- `POST /chat`
- `GET /chat/threads?bot_id=...`
- `POST /chat/threads`
- `PATCH /chat/threads/{thread_id}?bot_id=...`
- `DELETE /chat/threads/{thread_id}?bot_id=...`

### Analytics
- `GET /analytics/overview`

## Current Project Status

Implemented:
- auth flow
- multi-bot dashboard
- document upload + indexing
- hybrid RAG retrieval path
- persistent chat history
- bot settings
- widget preview
- API snippets
- analytics dashboard

Known reality:
- the retrieval system is still an active improvement area
- evaluation tooling exists for retrieval benchmarking
- the project is best treated as an active engineering build, not a finished SaaS

## Docs

- [architecture.md](docs/architecture.md)
- [api_docs.md](docs/api_docs.md)

---

<p align="center">
  <b>ChatDock</b> • document-aware chatbot project with hybrid retrieval and full-stack workflow
</p>
