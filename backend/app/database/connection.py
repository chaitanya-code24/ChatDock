from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generator, TYPE_CHECKING
from uuid import UUID, uuid4

from app.core.config import settings
from app.models.bot_model import BotRecord
from app.models.chat_model import ChatLogRecord
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
    chat_logs: dict[UUID, ChatLogRecord] = field(default_factory=dict)

    def reset(self) -> None:
        self.users.clear()
        self.users_by_email.clear()
        self.bots.clear()
        self.documents.clear()
        self.chunks.clear()
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


def get_db_session() -> Generator[SASession, None, None]:
    if SessionLocal is None:
        raise RuntimeError("Database session is unavailable")
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
