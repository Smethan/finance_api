from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.account import Account
from app.models.item import Item
from app.models.transaction import Transaction
from app.schemas.account import AccountBase, AccountDetail
from app.schemas.transaction import TransactionSummary

router = APIRouter(prefix="/v1/accounts", tags=["accounts"])


@router.get("/", response_model=List[AccountBase])
async def list_accounts(
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    stmt = (
        select(Account)
        .join(Item, Account.item_id == Item.id)
        .where(Item.user_id == current_user.id)
        .order_by(Account.name)
    )
    result = await session.execute(stmt)
    accounts = result.scalars().all()
    return accounts


@router.get("/{account_id}", response_model=AccountDetail)
async def get_account_detail(
    account_id: str,
    *,
    limit: int = Query(default=10, ge=0, le=100),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    account_stmt = (
        select(Account)
        .join(Item, Account.item_id == Item.id)
        .where(Account.id == account_id, Item.user_id == current_user.id)
    )
    account_result = await session.execute(account_stmt)
    account = account_result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    txn_stmt = (
        select(Transaction)
        .where(Transaction.account_id == account_id)
        .order_by(Transaction.date.desc())
        .limit(limit)
    )
    txn_result = await session.execute(txn_stmt)
    transactions = txn_result.scalars().all()

    account_data = AccountDetail.model_validate(account, from_attributes=True)
    return account_data.model_copy(
        update={
            "recent_transactions": [
                TransactionSummary.model_validate(txn, from_attributes=True) for txn in transactions
            ]
        }
    )
