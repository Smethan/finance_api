from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List

from pydantic import Field

from app.schemas.base import APIModel


class NetWorthHistoryPoint(APIModel):
    as_of_date: date
    net_worth: Decimal | None = None


class NetWorthResponse(APIModel):
    net_worth: Decimal | None = None
    assets: Decimal | None = None
    liabilities: Decimal | None = None
    history: List[NetWorthHistoryPoint] = Field(default_factory=list)


class CashflowResponse(APIModel):
    start_date: date
    end_date: date
    inflow: Decimal
    outflow: Decimal
    net: Decimal
