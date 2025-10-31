from __future__ import annotations

from typing import AsyncIterator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.services.auth import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/token")


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async for session in get_session():
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
):
    auth_service = AuthService(session)
    try:
        return await auth_service.get_user_from_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
