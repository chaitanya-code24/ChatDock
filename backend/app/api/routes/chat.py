from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import CurrentUserId
from app.core.rate_limiter import rate_limiter
from app.schemas.chat_schema import AnalyticsOverview, ChatRequest, ChatResponse, ChatThreadCreate, ChatThreadSummary, ChatThreadUpdate
from app.services.chat_service import chat_service

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, user_id: CurrentUserId) -> ChatResponse:
    rate_limiter.check(f"chat:{user_id}")
    answer, cached, sources, logs, conversation_id = chat_service.answer(
        user_id,
        payload.bot_id,
        payload.message,
        conversation_id=payload.conversation_id,
        bypass_cache=payload.nocache,
    )
    return ChatResponse(
        bot_id=payload.bot_id,
        conversation_id=conversation_id,
        answer=answer,
        cached=cached,
        sources=sources,
        logs=logs,
    )


@router.get("/chat/threads", response_model=list[ChatThreadSummary])
def list_chat_threads(bot_id: UUID, user_id: CurrentUserId) -> list[ChatThreadSummary]:
    return chat_service.list_threads(user_id, bot_id)


@router.post("/chat/threads", response_model=ChatThreadSummary, status_code=201)
def create_chat_thread(payload: ChatThreadCreate, user_id: CurrentUserId) -> ChatThreadSummary:
    return chat_service.create_thread(user_id, payload.bot_id, payload.title)


@router.patch("/chat/threads/{thread_id:uuid}", response_model=ChatThreadSummary)
def rename_chat_thread(thread_id: UUID, payload: ChatThreadUpdate, bot_id: UUID, user_id: CurrentUserId) -> ChatThreadSummary:
    return chat_service.rename_thread(user_id, bot_id, thread_id, payload.title)


@router.delete("/chat/threads/{thread_id:uuid}", response_model=dict[str, str])
def delete_chat_thread(thread_id: UUID, bot_id: UUID, user_id: CurrentUserId) -> dict[str, str]:
    chat_service.delete_thread(user_id, bot_id, thread_id)
    return {"status": "deleted"}


@router.get("/analytics/overview", response_model=AnalyticsOverview)
def analytics_overview(user_id: CurrentUserId, bot_id: UUID | None = None) -> AnalyticsOverview:
    return chat_service.analytics_overview(user_id, bot_id)
