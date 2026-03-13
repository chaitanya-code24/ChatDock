from fastapi import APIRouter

from app.api.dependencies import CurrentUserId
from app.core.rate_limiter import rate_limiter
from app.schemas.chat_schema import AnalyticsOverview, ChatRequest, ChatResponse
from app.services.chat_service import chat_service

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, user_id: CurrentUserId) -> ChatResponse:
    rate_limiter.check(f"chat:{user_id}")
    answer, cached, sources = chat_service.answer(user_id, payload.bot_id, payload.message)
    return ChatResponse(bot_id=payload.bot_id, answer=answer, cached=cached, sources=sources)


@router.get("/analytics/overview", response_model=AnalyticsOverview)
def analytics_overview(user_id: CurrentUserId) -> AnalyticsOverview:
    return chat_service.analytics_overview(user_id)
