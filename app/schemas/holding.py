from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from app.schemas.base import TimestampedModel
from app.schemas.security import SecuritySummary


class HoldingSummary(TimestampedModel):
    account_id: str
    security_id: str
    quantity: Decimal
    institution_value: Optional[Decimal] = None
    institution_price: Optional[Decimal] = None
    institution_price_as_of: Optional[date] = None
    cost_basis: Optional[Decimal] = None
    last_updated: Optional[datetime] = None
    security: Optional[SecuritySummary] = None
