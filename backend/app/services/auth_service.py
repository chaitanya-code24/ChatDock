from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select

from app.core.security import create_access_token, hash_password, verify_password
from app.database.connection import get_db_session, use_database, store
from app.database.models import UserORM
from app.models.user_model import UserRecord


class AuthService:
    def register(self, email: str, password: str) -> tuple[UserRecord, str]:
        normalized_email = email.strip().lower()
        if use_database():
            for db in get_db_session():
                existing = db.execute(select(UserORM).where(UserORM.email == normalized_email)).scalar_one_or_none()
                if existing is not None:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

                user_id = store.next_id()
                record = UserORM(
                    id=user_id,
                    email=normalized_email,
                    password_hash=hash_password(password),
                    created_at=datetime.now(timezone.utc),
                )
                db.add(record)
                db.commit()
                db.refresh(record)
                user = self._to_record(record)
                return user, create_access_token(user.id, user.email)

        if normalized_email in store.users_by_email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user = UserRecord(
            id=store.next_id(),
            email=normalized_email,
            password_hash=hash_password(password),
            created_at=datetime.now(timezone.utc),
        )
        store.users[user.id] = user
        store.users_by_email[normalized_email] = user.id
        return user, create_access_token(user.id, user.email)

    def login(self, email: str, password: str) -> tuple[UserRecord, str]:
        normalized_email = email.strip().lower()
        if use_database():
            for db in get_db_session():
                record = db.execute(select(UserORM).where(UserORM.email == normalized_email)).scalar_one_or_none()
                if record is None:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
                user = self._to_record(record)
                if not verify_password(password, user.password_hash):
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
                return user, create_access_token(user.id, user.email)

        user_id = store.users_by_email.get(normalized_email)
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        user = store.users[user_id]
        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        return user, create_access_token(user.id, user.email)

    def exists(self, user_id: UUID) -> bool:
        if use_database():
            for db in get_db_session():
                record = db.get(UserORM, user_id)
                return record is not None
        return user_id in store.users

    @staticmethod
    def _to_record(record: UserORM) -> UserRecord:
        return UserRecord(
            id=record.id,
            email=record.email,
            password_hash=record.password_hash,
            created_at=record.created_at,
        )


auth_service = AuthService()
