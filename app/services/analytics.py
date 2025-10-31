from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.balance_snapshot import BalanceSnapshot
from app.models.item import Item
from app.models.transaction import Transaction


@dataclass(slots=True)
class NetWorthSummary:
    net_worth: Decimal | None
    assets: Decimal | None
    liabilities: Decimal | None


@dataclass(slots=True)
class CashflowSummary:
    start_date: date
    end_date: date
    inflow: Decimal
    outflow: Decimal


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def net_worth(self, user_id: str) -> NetWorthSummary:
        asset_case = case(
            (Account.type.in_(["loan", "credit"]), 0),
            else_=Account.current_balance,
        )
        liability_case = case(
            (Account.type.in_(["loan", "credit"]), Account.current_balance),
            else_=0,
        )
        stmt = (
            select(
                func.sum(asset_case),
                func.sum(liability_case),
            )
            .select_from(Account)
            .join(Item, Account.item_id == Item.id)
            .where(Item.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        assets, liabilities = result.one()
        if assets is None and liabilities is None:
            return NetWorthSummary(net_worth=None, assets=None, liabilities=None)
        net_worth = (assets or Decimal("0")) - (liabilities or Decimal("0"))
        return NetWorthSummary(
            net_worth=net_worth,
            assets=assets,
            liabilities=liabilities,
        )

    async def cashflow_summary(
        self,
        user_id: str,
        *,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> CashflowSummary:
        end = end_date or date.today()
        start = start_date or (end - timedelta(days=30))

        inflow_case = case(
            (Transaction.amount < 0, -Transaction.amount),
            else_=0,
        )
        outflow_case = case(
            (Transaction.amount > 0, Transaction.amount),
            else_=0,
        )

        stmt = (
            select(func.sum(inflow_case), func.sum(outflow_case))
            .select_from(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .join(Item, Account.item_id == Item.id)
            .where(
                Item.user_id == user_id,
                Transaction.date >= start,
                Transaction.date <= end,
            )
        )
        result = await self.session.execute(stmt)
        inflow, outflow = result.one()
        inflow = inflow or Decimal("0")
        outflow = outflow or Decimal("0")
        return CashflowSummary(
            start_date=start,
            end_date=end,
            inflow=inflow,
            outflow=abs(outflow),
        )

    async def recent_net_worth(self, user_id: str, *, limit: int = 90) -> list[tuple[date, Decimal]]:
        stmt = (
            select(BalanceSnapshot.as_of_date, BalanceSnapshot.net_worth)
            .where(BalanceSnapshot.user_id == user_id)
            .order_by(BalanceSnapshot.as_of_date.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [(row.as_of_date, row.net_worth) for row in result]
