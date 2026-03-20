from uuid import UUID

from fastapi import APIRouter, File, UploadFile
from sqlalchemy import func, select

from app.api.dependencies import CurrentUserId
from app.core.rate_limiter import rate_limiter
from app.database.connection import get_db_session, store, use_database
from app.database.models import ChunkORM
from app.schemas.document_schema import DocumentSummary
from app.services.bot_service import bot_service
from app.services.document_service import document_service

router = APIRouter(prefix="/bot", tags=["document"])


@router.post("/upload", response_model=DocumentSummary, status_code=201)
async def upload_document(
    bot_id: UUID,
    user_id: CurrentUserId,
    file: UploadFile = File(...)
) -> DocumentSummary:

    # Allow more frequent upload requests for documents while keeping chat limits stricter.
    rate_limiter.check(f"document-upload:{user_id}", limit=120, window_seconds=60)

    bot = bot_service.get_owned(user_id, bot_id)

    document, chunks = await document_service.ingest(bot.id, file)

    return DocumentSummary(
        id=document.id,
        bot_id=document.bot_id,
        file_name=document.file_name,
        uploaded_at=document.uploaded_at,
        chunk_count=len(chunks),
        mime_type=document.mime_type,
    )


@router.get("/documents", response_model=list[DocumentSummary])
def list_documents(
    bot_id: UUID,
    user_id: CurrentUserId
) -> list[DocumentSummary]:

    rate_limiter.check(f"document-list:{user_id}")

    bot = bot_service.get_owned(user_id, bot_id)

    documents = document_service.list_for_bot(bot.id)

    document_summaries: list[DocumentSummary] = []

    for document in documents:

        chunk_count = 0

        if use_database():
            for db in get_db_session():
                chunk_count = db.execute(
                    select(func.count())
                    .select_from(ChunkORM)
                    .where(ChunkORM.document_id == document.id)
                ).scalar_one()
        else:
            chunk_count = sum(
                1 for chunk in store.chunks.values()
                if chunk.document_id == document.id
            )

        document_summaries.append(
            DocumentSummary(
                id=document.id,
                bot_id=document.bot_id,
                file_name=document.file_name,
                uploaded_at=document.uploaded_at,
                chunk_count=int(chunk_count),
                mime_type=document.mime_type,
            )
        )

    return document_summaries


@router.delete("/document/{document_id}", response_model=dict[str, str])
def delete_document(
    document_id: UUID,
    bot_id: UUID,
    user_id: CurrentUserId
) -> dict[str, str]:

    rate_limiter.check(f"document-delete:{user_id}")

    bot = bot_service.get_owned(user_id, bot_id)
    document_service.delete(bot.id, document_id)

    return {"status": "deleted"}
