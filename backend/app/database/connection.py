from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generator, TYPE_CHECKING
from uuid import UUID, uuid4

from app.core.config import settings
from app.models.bot_model import BotRecord
from app.models.chat_model import ChatLogRecord, ChatThreadRecord
from app.models.document_model import ChunkRecord, DocumentRecord
from app.models.user_model import UserRecord

try:
    from sqlalchemy import create_engine, text  # type: ignore
    from sqlalchemy.orm import declarative_base, sessionmaker  # type: ignore
except ImportError:  # pragma: no cover
    create_engine = None
    declarative_base = None
    sessionmaker = None
    text = None

if TYPE_CHECKING:
    from sqlalchemy.orm import Session as SASession
else:
    SASession = Any


@dataclass(slots=True)
class InMemoryStore:
    users: dict[UUID, UserRecord] = field(default_factory=dict)
    users_by_email: dict[str, UUID] = field(default_factory=dict)
    bots: dict[UUID, BotRecord] = field(default_factory=dict)
    documents: dict[UUID, DocumentRecord] = field(default_factory=dict)
    chunks: dict[UUID, ChunkRecord] = field(default_factory=dict)
    chat_threads: dict[UUID, ChatThreadRecord] = field(default_factory=dict)
    chat_logs: dict[UUID, ChatLogRecord] = field(default_factory=dict)

    def reset(self) -> None:
        self.users.clear()
        self.users_by_email.clear()
        self.bots.clear()
        self.documents.clear()
        self.chunks.clear()
        self.chat_threads.clear()
        self.chat_logs.clear()

    @staticmethod
    def next_id() -> UUID:
        return uuid4()


store = InMemoryStore()

# SQLAlchemy plumbing for production persistence.
Base = declarative_base() if declarative_base is not None else None
engine = create_engine(settings.database_url, pool_pre_ping=True) if create_engine is not None else None
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False) if sessionmaker is not None else None
_database_available: bool | None = None


def init_db() -> None:
    global _database_available
    # Startup hook only checks connectivity. Schema changes should go through Alembic.
    _database_available = None
    _database_available = use_database()
    if _database_available:
        # Import models before create_all so SQLAlchemy knows about every table.
        from app.database import models  # noqa: F401

        if Base is not None and engine is not None:
            Base.metadata.create_all(bind=engine)
        _ensure_runtime_schema()


def use_database() -> bool:
    global _database_available
    if SessionLocal is None or engine is None or text is None:
        return False
    if _database_available is not None:
        return _database_available
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        _database_available = True
    except Exception:
        _database_available = False
    return _database_available


def _ensure_runtime_schema() -> None:
    if engine is None or text is None:
        return

    statements = [
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS archived BOOLEAN NOT NULL DEFAULT false",
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS tone VARCHAR(20) NOT NULL DEFAULT 'professional'",
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS answer_length VARCHAR(20) NOT NULL DEFAULT 'balanced'",
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS fallback_behavior VARCHAR(20) NOT NULL DEFAULT 'strict'",
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS system_prompt TEXT",
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS greeting_message TEXT",
        "ALTER TABLE bots ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ",
        "UPDATE bots SET updated_at = COALESCE(updated_at, created_at)",
        "ALTER TABLE chat_logs ADD COLUMN IF NOT EXISTS conversation_id UUID",
        "UPDATE chat_logs SET conversation_id = COALESCE(conversation_id, id)",
        "CREATE TABLE IF NOT EXISTS chat_threads (id UUID PRIMARY KEY, bot_id UUID NOT NULL REFERENCES bots(id), user_id UUID NOT NULL REFERENCES users(id), title VARCHAR(160) NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())",
        "CREATE INDEX IF NOT EXISTS ix_chat_logs_conversation_id ON chat_logs (conversation_id)",
        "CREATE INDEX IF NOT EXISTS ix_chat_threads_bot_id ON chat_threads (bot_id)",
        "CREATE INDEX IF NOT EXISTS ix_chat_threads_user_id ON chat_threads (user_id)",
        "INSERT INTO chat_threads (id, bot_id, user_id, title, created_at, updated_at) SELECT DISTINCT chat_logs.conversation_id, chat_logs.bot_id, chat_logs.user_id, LEFT(chat_logs.question, 160), MIN(chat_logs.timestamp), MAX(chat_logs.timestamp) FROM chat_logs LEFT JOIN chat_threads ON chat_threads.id = chat_logs.conversation_id WHERE chat_logs.conversation_id IS NOT NULL AND chat_threads.id IS NULL GROUP BY chat_logs.conversation_id, chat_logs.bot_id, chat_logs.user_id, LEFT(chat_logs.question, 160)",
    ]

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def get_db_session() -> Generator[SASession, None, None]:
    if SessionLocal is None:
        raise RuntimeError("Database session is unavailable")
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
