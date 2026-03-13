from fastapi import APIRouter

from app.schemas.user_schema import AuthResponse, UserCreate, UserLogin
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(payload: UserCreate) -> AuthResponse:
    user, token = auth_service.register(payload.email, payload.password)
    return AuthResponse(access_token=token, user_id=user.id, email=user.email)


@router.post("/login", response_model=AuthResponse)
def login(payload: UserLogin) -> AuthResponse:
    user, token = auth_service.login(payload.email, payload.password)
    return AuthResponse(access_token=token, user_id=user.id, email=user.email)

