from __future__ import annotations

from decimal import Decimal
import uuid

from sqlalchemy import ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        Index("ix_accounts_plaid_account_id_unique", "plaid_account_id", unique=True),
    )

    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("items.id"), nullable=False)
    plaid_account_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(128))
    official_name: Mapped[str | None] = mapped_column(String(256))
    mask: Mapped[str | None] = mapped_column(String(8))
    type: Mapped[str | None] = mapped_column(String(32))
    subtype: Mapped[str | None] = mapped_column(String(32))
    verification_status: Mapped[str | None] = mapped_column(String(32))
    iso_currency_code: Mapped[str | None] = mapped_column(String(3))

    current_balance: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    available_balance: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    item: Mapped["Item"] = relationship("Item", back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )
    holdings: Mapped[list["Holding"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"Account(plaid_account_id={self.plaid_account_id}, name={self.name})"
