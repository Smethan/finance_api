from __future__ import annotations

from typing import Iterable

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.security import encrypt_string
from app.services.plaid import PlaidService, plaid_service
from app.services.repositories import ItemRepository

router = APIRouter(prefix="/v1/plaid", tags=["plaid"])


class LinkTokenRequest(BaseModel):
    products: list[str] | None = None


class LinkTokenResponse(BaseModel):
    link_token: str


@router.post("/link-token", response_model=LinkTokenResponse)
async def create_link_token(
    payload: LinkTokenRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
    plaid: PlaidService = Depends(lambda: plaid_service),
):
    token = await plaid.create_link_token(str(current_user.id), products=payload.products)
    return LinkTokenResponse(link_token=token)


class PublicTokenExchangeRequest(BaseModel):
    public_token: str
    institution_id: str | None = None
    institution_name: str | None = None


@router.post("/item/public-token/exchange")
async def exchange_public_token(
    payload: PublicTokenExchangeRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
    plaid: PlaidService = Depends(lambda: plaid_service),
):
    exchange = await plaid.exchange_public_token(payload.public_token)
    encrypted_token = encrypt_string(exchange["access_token"])
    repo = ItemRepository(session)
    await repo.upsert(
        user_id=str(current_user.id),
        plaid_item_id=exchange["item_id"],
        access_token_encrypted=encrypted_token,
        institution_id=payload.institution_id,
        institution_name=payload.institution_name,
        webhook_status=None,
        cursor=None,
    )
    return {"status": "linked"}
