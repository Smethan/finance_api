from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import Field

from app.schemas.base import TimestampedModel
from app.schemas.transaction import TransactionSummary


class AccountBase(TimestampedModel):
    item_id: str
    plaid_account_id: str
    name: Optional[str] = None
    official_name: Optional[str] = None
    mask: Optional[str] = None
    type: Optional[str] = None
    subtype: Optional[str] = None
    verification_status: Optional[str] = None
    iso_currency_code: Optional[str] = None
    current_balance: Optional[Decimal] = None
    available_balance: Optional[Decimal] = None
    limit: Optional[Decimal] = None


class AccountDetail(AccountBase):
    recent_transactions: List[TransactionSummary] = Field(default_factory=list)
