from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from app.schemas.base import TimestampedModel


class NetWorthSnapshot(TimestampedModel):
    user_id: str
    as_of_date: date
    net_worth: Optional[Decimal] = None
    liquid_assets: Optional[Decimal] = None
    investments: Optional[Decimal] = None
    liabilities: Optional[Decimal] = None
    cash_flow_in: Optional[Decimal] = None
    cash_flow_out: Optional[Decimal] = None
