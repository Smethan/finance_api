from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.account import Account
from app.models.holding import Holding
from app.models.item import Item
from app.models.security import Security
from app.schemas.holding import HoldingSummary
from app.schemas.security import SecuritySummary

router = APIRouter(prefix="/v1/holdings", tags=["holdings"])


@router.get("/", response_model=List[HoldingSummary])
async def list_holdings(
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    stmt = (
        select(Holding, Security)
        .join(Account, Holding.account_id == Account.id)
        .join(Item, Account.item_id == Item.id)
        .join(Security, Holding.security_id == Security.id)
        .where(Item.user_id == current_user.id)
        .order_by(Security.ticker_symbol)
    )
    result = await session.execute(stmt)

    holdings: list[HoldingSummary] = []
    for holding, security in result:
        holding_model = HoldingSummary.model_validate(holding, from_attributes=True)
        security_model = SecuritySummary.model_validate(security, from_attributes=True)
        holdings.append(
            holding_model.model_copy(update={"security": security_model})
        )
    return holdings
