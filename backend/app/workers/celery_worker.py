from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "chatdock",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    task_routes={
        "app.workers.tasks.process_document_task": {"queue": "documents"},
    },
)
