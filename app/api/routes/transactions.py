from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.account import Account
from app.models.item import Item
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionSummary

router = APIRouter(prefix="/v1/transactions", tags=["transactions"])


@router.get("/", response_model=List[TransactionSummary])
async def list_transactions(
    *,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    account_id: Optional[str] = Query(default=None),
    include_pending: bool = Query(default=True),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    stmt = (
        select(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .join(Item, Account.item_id == Item.id)
        .where(Item.user_id == current_user.id)
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    conditions = []
    if account_id:
        conditions.append(Transaction.account_id == account_id)
    if start_date:
        conditions.append(Transaction.date >= start_date)
    if end_date:
        conditions.append(Transaction.date <= end_date)
    if not include_pending:
        conditions.append(Transaction.pending.is_(False))

    if conditions:
        stmt = stmt.where(and_(*conditions))

    result = await session.execute(stmt)
    transactions = result.scalars().all()
    return [TransactionSummary.model_validate(txn, from_attributes=True) for txn in transactions]
