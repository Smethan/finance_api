from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import Field

from app.schemas.base import APIModel, TimestampedModel


class TransactionBase(TimestampedModel):
    account_id: str
    plaid_transaction_id: str
    amount: Decimal
    iso_currency_code: Optional[str] = None
    date: Optional[date] = None
    authorized_date: Optional[date] = None
    name: Optional[str] = None
    merchant_name: Optional[str] = None
    transaction_type: Optional[str] = None
    pending: bool = False
    payment_channel: Optional[str] = None
    category: Optional[List[str]] = None
    personal_finance_category: Optional[dict] = None
    counterparty: Optional[dict] = None
    transaction_id: Optional[str] = None
    transaction_code: Optional[str] = None
    last_modified_at: Optional[datetime] = None


class TransactionSummary(TransactionBase):
    pass


class TransactionDetail(TransactionBase):
    notes: Optional[str] = Field(default=None, description="Optional manually added notes")
