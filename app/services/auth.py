from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, decode_access_token
from app.models.user import User
from app.services.repositories import UserRepository


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def issue_token(self, email: str, external_id: str | None = None) -> Dict[str, str]:
        user = await self.users.get_or_create(email, external_id)
        token = create_access_token(subject=str(user.id))
        return {"access_token": token, "token_type": "bearer"}

    async def get_user_from_token(self, token: str) -> User:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")
        repo = UserRepository(self.session)
        result = await self.session.get(User, user_id)
        if result is None:
            raise ValueError("User not found for token")
        return result
