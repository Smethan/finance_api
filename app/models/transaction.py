from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import uuid

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_plaid_transaction_id_unique", "plaid_transaction_id", unique=True),
        Index("ix_transactions_account_date", "account_id", "date"),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    plaid_transaction_id: Mapped[str] = mapped_column(String(128), nullable=False)
    transaction_code: Mapped[str | None] = mapped_column(String(32))
    # Plaid may provide transaction_id as stable identifier
    transaction_id: Mapped[str | None] = mapped_column(String(128))
    name: Mapped[str | None] = mapped_column(String(256))
    merchant_name: Mapped[str | None] = mapped_column(String(256))
    transaction_type: Mapped[str | None] = mapped_column(String(32))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    iso_currency_code: Mapped[str | None] = mapped_column(String(3))
    date: Mapped[date | None] = mapped_column(Date)
    authorized_date: Mapped[date | None] = mapped_column(Date)
    pending: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_channel: Mapped[str | None] = mapped_column(String(32))
    personal_finance_category: Mapped[dict | None] = mapped_column(JSON)
    category: Mapped[list[str] | None] = mapped_column(JSON)
    counterparty: Mapped[dict | None] = mapped_column(JSON)
    last_modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    account: Mapped["Account"] = relationship("Account", back_populates="transactions")

    def __repr__(self) -> str:
        return f"Transaction(plaid_transaction_id={self.plaid_transaction_id})"
