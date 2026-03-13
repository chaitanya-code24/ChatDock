from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status

from app.core.security import decode_access_token
from app.services.auth_service import auth_service


def get_current_user_id(authorization: Annotated[str | None, Header()] = None) -> UUID:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    payload = decode_access_token(authorization.removeprefix("Bearer ").strip())
    user_id = UUID(str(payload["sub"]))
    if not auth_service.exists(user_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown user")
    return user_id


CurrentUserId = Annotated[UUID, Depends(get_current_user_id)]
