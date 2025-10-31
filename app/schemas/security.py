from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from app.schemas.base import TimestampedModel


class SecuritySummary(TimestampedModel):
    plaid_security_id: str
    name: Optional[str] = None
    ticker_symbol: Optional[str] = None
    isin: Optional[str] = None
    cusip: Optional[str] = None
    type: Optional[str] = None
    close_price: Optional[Decimal] = None
    close_price_date: Optional[date] = None
    currency: Optional[str] = None
