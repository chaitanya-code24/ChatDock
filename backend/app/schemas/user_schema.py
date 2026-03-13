from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def _normalize_email(value: str) -> str:
    normalized = value.strip().lower()
    if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        raise ValueError("A valid email address is required")
    return normalized


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)

    _validate_email = field_validator("email")(_normalize_email)


class UserLogin(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)

    _validate_email = field_validator("email")(_normalize_email)


class AuthResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user_id: UUID
    email: str

