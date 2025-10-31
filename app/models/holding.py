from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import uuid

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Holding(Base):
    __tablename__ = "holdings"
    __table_args__ = (
        Index(
            "ix_holdings_account_security_unique",
            "account_id",
            "security_id",
            unique=True,
        ),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    security_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("securities.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    institution_value: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    institution_price: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    institution_price_as_of: Mapped[date | None] = mapped_column(Date)
    cost_basis: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    last_updated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    account: Mapped["Account"] = relationship("Account", back_populates="holdings")
    security: Mapped["Security"] = relationship("Security", back_populates="holdings")

    def __repr__(self) -> str:
        return (
            f"Holding(account_id={self.account_id}, security_id={self.security_id}, quantity={self.quantity})"
        )
