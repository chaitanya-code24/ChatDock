from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.bot import router as bot_router
from app.api.routes.chat import router as chat_router
from app.api.routes.document import router as document_router
from app.core.config import settings
from app.database.connection import init_db
from app.schemas.chat_schema import HealthResponse

app = FastAPI(
    title=settings.project_name,
    summary="Document-trained chatbot builder backend",
    version="0.1.0",
)

default_cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    "https://chat-dock.vercel.app",
    "https://chat-dock-chaitanya-lokhandes-projects.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or default_cors_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
def root() -> HealthResponse:
    return HealthResponse(
        project_name=settings.project_name,
        max_context_chunks=settings.max_context_chunks,
        chunk_size_tokens=settings.chunk_size_tokens,
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return root()


app.include_router(auth_router)
app.include_router(bot_router)
app.include_router(document_router)
app.include_router(chat_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
