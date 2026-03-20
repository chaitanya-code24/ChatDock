from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, UploadFile, status

from sqlalchemy import delete, func, select

from app.core.config import settings
from app.database.connection import get_db_session, use_database, store
from app.database.models import ChunkORM, DocumentORM
from app.models.document_model import ChunkRecord, DocumentRecord
from app.rag.chunking import chunk_text, estimate_token_count
from app.rag.document_processor import build_structured_chunks
from app.rag.vector_store import vector_store
from app.utils.file_parser import parse_document
from app.utils.text_cleaner import clean_text


class DocumentService:
    supported_extensions = {".txt", ".md", ".pdf", ".docx"}

    async def ingest(self, bot_id: UUID, upload: UploadFile) -> tuple[DocumentRecord, list[ChunkRecord]]:
        suffix = self._suffix(upload.filename or "")
        if suffix not in self.supported_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type. Use PDF, TXT, DOCX, or MD.",
            )

        payload = await upload.read()
        parsed_text = parse_document(upload.filename or "document", suffix, payload)
        raw_text = parsed_text.strip()
        if not raw_text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document did not contain readable text")

        structured_chunks = build_structured_chunks(raw_text, source=upload.filename or "document")
        storage_chunks = [chunk.to_storage_text() for chunk in structured_chunks]
        if not storage_chunks:
            storage_chunks = chunk_text(clean_text(raw_text), settings.chunk_size_tokens, settings.chunk_overlap)

        if use_database():
            for db in get_db_session():
                document_id = store.next_id()
                document_row = DocumentORM(
                    id=document_id,
                    bot_id=bot_id,
                    file_name=upload.filename or "document",
                    mime_type=upload.content_type or "application/octet-stream",
                    raw_text=raw_text,
                    uploaded_at=datetime.now(timezone.utc),
                )
                db.add(document_row)
                db.flush()

                chunk_rows: list[ChunkORM] = []
                chunk_records: list[ChunkRecord] = []
                for chunk_text_value in storage_chunks:
                    chunk_id = store.next_id()
                    chunk_row = ChunkORM(
                        id=chunk_id,
                        document_id=document_id,
                        bot_id=bot_id,
                        text=chunk_text_value,
                        token_count=estimate_token_count(chunk_text_value),
                    )
                    db.add(chunk_row)
                    chunk_rows.append(chunk_row)
                    chunk_records.append(
                        ChunkRecord(
                            id=chunk_id,
                            document_id=document_id,
                            bot_id=bot_id,
                            text=chunk_text_value,
                            token_count=chunk_row.token_count,
                        )
                    )
                db.commit()

                document = DocumentRecord(
                    id=document_row.id,
                    bot_id=document_row.bot_id,
                    file_name=document_row.file_name,
                    mime_type=document_row.mime_type,
                    raw_text=document_row.raw_text,
                    uploaded_at=document_row.uploaded_at,
                )
                vector_store.upsert_bot_chunks(bot_id)
                return document, chunk_records

        document = DocumentRecord(
            id=store.next_id(),
            bot_id=bot_id,
            file_name=upload.filename or "document",
            mime_type=upload.content_type or "application/octet-stream",
            raw_text=raw_text,
            uploaded_at=datetime.now(timezone.utc),
        )
        store.documents[document.id] = document

        chunk_records: list[ChunkRecord] = []
        for chunk_text_value in storage_chunks:
            chunk = ChunkRecord(
                id=store.next_id(),
                document_id=document.id,
                bot_id=bot_id,
                text=chunk_text_value,
                token_count=estimate_token_count(chunk_text_value),
            )
            store.chunks[chunk.id] = chunk
            chunk_records.append(chunk)

        # Sync latest chunks to vector database when available.
        vector_store.upsert_bot_chunks(bot_id)
        return document, chunk_records

    @staticmethod
    def _suffix(file_name: str) -> str:
        lowered = file_name.lower()
        dot_index = lowered.rfind(".")
        return lowered[dot_index:] if dot_index != -1 else ""


    def list_for_bot(self, bot_id: UUID) -> list[DocumentRecord]:
        if use_database():
            documents: list[DocumentRecord] = []
            for db in get_db_session():
                rows = db.execute(select(DocumentORM).where(DocumentORM.bot_id == bot_id)).scalars().all()
                for row in rows:
                    documents.append(
                        DocumentRecord(
                            id=row.id,
                            bot_id=row.bot_id,
                            file_name=row.file_name,
                            mime_type=row.mime_type,
                            raw_text=row.raw_text,
                            uploaded_at=row.uploaded_at,
                        )
                    )
            return documents

        return [doc for doc in store.documents.values() if doc.bot_id == bot_id]

    def delete(self, bot_id: UUID, document_id: UUID) -> None:
        if use_database():
            for db in get_db_session():
                document = db.get(DocumentORM, document_id)
                if document is None or document.bot_id != bot_id:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
                db.execute(delete(ChunkORM).where(ChunkORM.document_id == document_id))
                db.delete(document)
                db.commit()
                vector_store.upsert_bot_chunks(bot_id)
                return

        document = store.documents.get(document_id)
        if document is None or document.bot_id != bot_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        chunk_ids = [chunk_id for chunk_id, chunk in store.chunks.items() if chunk.document_id == document_id]
        for chunk_id in chunk_ids:
            store.chunks.pop(chunk_id, None)
        store.documents.pop(document_id, None)
        vector_store.upsert_bot_chunks(bot_id)


document_service = DocumentService()
