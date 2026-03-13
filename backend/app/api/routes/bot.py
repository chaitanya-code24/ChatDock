from fastapi import APIRouter
from uuid import UUID

from app.api.dependencies import CurrentUserId
from app.core.rate_limiter import rate_limiter
from app.schemas.bot_schema import BotCreate, BotSummary
from app.services.bot_service import bot_service

router = APIRouter(prefix="/bot", tags=["bot"])


@router.post("/create", response_model=BotSummary, status_code=201)
def create_bot(payload: BotCreate, user_id: CurrentUserId) -> BotSummary:
    rate_limiter.check(f"bot-create:{user_id}")
    bot = bot_service.create(user_id, payload.bot_name, payload.description)
    return bot_service.to_summary(bot.id)


@router.get("/list", response_model=list[BotSummary])
def list_bots(user_id: CurrentUserId) -> list[BotSummary]:
    bots = bot_service.list_for_user(user_id)
    return [bot_service.to_summary(bot.id) for bot in bots]


@router.delete("/{bot_id}", response_model=dict[str, str])
def delete_bot(bot_id: UUID, user_id: CurrentUserId) -> dict[str, str]:
    rate_limiter.check(f"bot-delete:{user_id}")
    bot_service.delete_owned(user_id, bot_id=bot_id)
    return {"status": "deleted"}
