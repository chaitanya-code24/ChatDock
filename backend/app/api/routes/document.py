from uuid import UUID

from fastapi import APIRouter, File, UploadFile

from app.api.dependencies import CurrentUserId
from app.core.rate_limiter import rate_limiter
from app.schemas.document_schema import DocumentSummary
from app.services.bot_service import bot_service
from app.services.document_service import document_service

router = APIRouter(prefix="/bot", tags=["document"])


@router.post("/upload", response_model=DocumentSummary, status_code=201)
async def upload_document(
    bot_id: str,
    user_id: CurrentUserId,
    file: UploadFile = File(...),
) -> DocumentSummary:
    rate_limiter.check(f"document-upload:{user_id}")
    bot = bot_service.get_owned(user_id, UUID(bot_id))
    document, chunks = await document_service.ingest(bot.id, file)
    return DocumentSummary(
        id=document.id,
        bot_id=document.bot_id,
        file_name=document.file_name,
        uploaded_at=document.uploaded_at,
        chunk_count=len(chunks),
        mime_type=document.mime_type,
    )

