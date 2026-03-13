from app.utils.logger import get_logger
from app.workers.celery_worker import celery_app

logger = get_logger("workers.tasks")


@celery_app.task(name="app.workers.tasks.process_document_task")
def process_document_task(bot_id: str, file_name: str) -> dict[str, str]:
    # Placeholder task until document upload is moved to async queue ingestion.
    logger.info("Queued document processing for bot=%s file=%s", bot_id, file_name)
    return {"status": "queued", "bot_id": bot_id, "file_name": file_name}
