from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Security(Base):
    __tablename__ = "securities"
    __table_args__ = (
        Index("ix_securities_plaid_security_id_unique", "plaid_security_id", unique=True),
    )

    plaid_security_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str | None] = mapped_column(String(256))
    ticker_symbol: Mapped[str | None] = mapped_column(String(32))
    isin: Mapped[str | None] = mapped_column(String(32))
    cusip: Mapped[str | None] = mapped_column(String(16))
    type: Mapped[str | None] = mapped_column(String(64))
    close_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    close_price_date: Mapped[date | None] = mapped_column(Date)
    currency: Mapped[str | None] = mapped_column(String(3))

    holdings: Mapped[list["Holding"]] = relationship(
        back_populates="security",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"Security(plaid_security_id={self.plaid_security_id})"
