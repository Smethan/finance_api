from __future__ import annotations

from datetime import date
from decimal import Decimal
import uuid

from sqlalchemy import Date, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BalanceSnapshot(Base):
    __tablename__ = "balance_snapshots"
    __table_args__ = (
        Index("ix_balance_snapshots_user_date_unique", "user_id", "as_of_date", unique=True),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    net_worth: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    liquid_assets: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    investments: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    liabilities: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    cash_flow_in: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    cash_flow_out: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"BalanceSnapshot(user_id={self.user_id}, date={self.as_of_date})"
