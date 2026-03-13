from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select

from app.database.connection import get_db_session, use_database, store
from app.database.models import BotORM, ChatLogORM, ChunkORM, DocumentORM
from app.models.bot_model import BotRecord
from app.schemas.bot_schema import BotSummary


class BotService:
    def create(self, user_id: UUID, bot_name: str, description: str | None) -> BotRecord:
        if use_database():
            for db in get_db_session():
                record = BotORM(
                    id=store.next_id(),
                    user_id=user_id,
                    bot_name=bot_name.strip(),
                    description=description.strip() if description else None,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(record)
                db.commit()
                db.refresh(record)
                return self._to_record(record)

        bot = BotRecord(
            id=store.next_id(),
            user_id=user_id,
            bot_name=bot_name.strip(),
            description=description.strip() if description else None,
            created_at=datetime.now(timezone.utc),
        )
        store.bots[bot.id] = bot
        return bot

    def list_for_user(self, user_id: UUID) -> list[BotRecord]:
        if use_database():
            for db in get_db_session():
                records = db.execute(select(BotORM).where(BotORM.user_id == user_id)).scalars().all()
                return [self._to_record(record) for record in records]
        return [bot for bot in store.bots.values() if bot.user_id == user_id]

    def get_owned(self, user_id: UUID, bot_id: UUID) -> BotRecord:
        if use_database():
            for db in get_db_session():
                record = db.get(BotORM, bot_id)
                if record is None or record.user_id != user_id:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")
                return self._to_record(record)

        bot = store.bots.get(bot_id)
        if bot is None or bot.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")
        return bot

    def to_summary(self, bot_id: UUID) -> BotSummary:
        if use_database():
            for db in get_db_session():
                record = db.get(BotORM, bot_id)
                if record is None:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")
                document_count = db.execute(
                    select(func.count()).select_from(DocumentORM).where(DocumentORM.bot_id == bot_id)
                ).scalar_one()
                chunk_count = db.execute(
                    select(func.count()).select_from(ChunkORM).where(ChunkORM.bot_id == bot_id)
                ).scalar_one()
                return BotSummary(
                    id=record.id,
                    user_id=record.user_id,
                    bot_name=record.bot_name,
                    description=record.description,
                    created_at=record.created_at,
                    document_count=int(document_count),
                    chunk_count=int(chunk_count),
                )

        bot = store.bots[bot_id]
        document_count = sum(1 for document in store.documents.values() if document.bot_id == bot_id)
        chunk_count = sum(1 for chunk in store.chunks.values() if chunk.bot_id == bot_id)
        return BotSummary(
            id=bot.id,
            user_id=bot.user_id,
            bot_name=bot.bot_name,
            description=bot.description,
            created_at=bot.created_at,
            document_count=document_count,
            chunk_count=chunk_count,
        )

    def delete_owned(self, user_id: UUID, bot_id: UUID) -> None:
        if use_database():
            for db in get_db_session():
                bot = db.get(BotORM, bot_id)
                if bot is None or bot.user_id != user_id:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")

                db.execute(delete(ChatLogORM).where(ChatLogORM.bot_id == bot_id))
                db.execute(delete(ChunkORM).where(ChunkORM.bot_id == bot_id))
                db.execute(delete(DocumentORM).where(DocumentORM.bot_id == bot_id))
                db.delete(bot)
                db.commit()
                return

        bot = store.bots.get(bot_id)
        if bot is None or bot.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")

        store.bots.pop(bot_id, None)
        document_ids = [document_id for document_id, document in store.documents.items() if document.bot_id == bot_id]
        for document_id in document_ids:
            store.documents.pop(document_id, None)
        chunk_ids = [chunk_id for chunk_id, chunk in store.chunks.items() if chunk.bot_id == bot_id]
        for chunk_id in chunk_ids:
            store.chunks.pop(chunk_id, None)
        log_ids = [log_id for log_id, log in store.chat_logs.items() if log.bot_id == bot_id]
        for log_id in log_ids:
            store.chat_logs.pop(log_id, None)

    @staticmethod
    def _to_record(record: BotORM) -> BotRecord:
        return BotRecord(
            id=record.id,
            user_id=record.user_id,
            bot_name=record.bot_name,
            description=record.description,
            created_at=record.created_at,
        )


bot_service = BotService()
