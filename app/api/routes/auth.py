from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.services.auth import AuthService

router = APIRouter(prefix="/v1/auth", tags=["auth"])


class TokenRequest(BaseModel):
    email: EmailStr
    external_id: str | None = None


@router.post("/token")
async def issue_token(
    payload: TokenRequest,
    session: AsyncSession = Depends(get_db_session),
):
    auth_service = AuthService(session)
    try:
        return await auth_service.issue_token(payload.email, payload.external_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
