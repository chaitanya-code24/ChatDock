from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status

from app.core.config import settings


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    salt, expected = stored_hash.split("$", maxsplit=1)
    candidate = hash_password(password, salt).split("$", maxsplit=1)[1]
    return hmac.compare_digest(candidate, expected)


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(user_id: UUID, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": int((datetime.now(timezone.utc) + timedelta(seconds=settings.auth_token_ttl_seconds)).timestamp()),
    }
    encoded_payload = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(
        settings.secret_key.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{encoded_payload}.{signature}"


def decode_access_token(token: str) -> dict[str, str | int]:
    try:
        encoded_payload, signature = token.split(".", maxsplit=1)
    except ValueError as exc:
        raise _unauthorized("Malformed access token") from exc

    expected_signature = hmac.new(
        settings.secret_key.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        raise _unauthorized("Invalid access token signature")

    payload = json.loads(_b64decode(encoded_payload).decode("utf-8"))
    if int(payload["exp"]) < int(datetime.now(timezone.utc).timestamp()):
        raise _unauthorized("Access token expired")
    return payload


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)

