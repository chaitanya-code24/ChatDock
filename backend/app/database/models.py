from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class BotORM(Base):
    __tablename__ = "bots"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    bot_name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(String(400), nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    tone: Mapped[str] = mapped_column(String(20), default="professional")
    answer_length: Mapped[str] = mapped_column(String(20), default="balanced")
    fallback_behavior: Mapped[str] = mapped_column(String(20), default="strict")
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    greeting_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DocumentORM(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True)
    bot_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("bots.id"), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(120))
    raw_text: Mapped[str] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ChunkORM(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True)
    document_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), index=True)
    bot_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("bots.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer, default=0)


class ChatLogORM(Base):
    __tablename__ = "chat_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(UUID(as_uuid=True), index=True)
    bot_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("bots.id"), index=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    response: Mapped[str] = mapped_column(Text)
    cached: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ChatThreadORM(Base):
    __tablename__ = "chat_threads"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True)
    bot_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("bots.id"), index=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

