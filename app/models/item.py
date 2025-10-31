from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        Index("ix_items_plaid_item_id_unique", "plaid_item_id", unique=True),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    plaid_item_id: Mapped[str] = mapped_column(String(128), nullable=False)
    institution_id: Mapped[str | None] = mapped_column(String(64))
    institution_name: Mapped[str | None] = mapped_column(String(128))
    access_token_encrypted: Mapped[str] = mapped_column(String(512), nullable=False)
    webhook_status: Mapped[str | None] = mapped_column(String(32))
    cursor: Mapped[str | None] = mapped_column(String(256))
    last_successful_sync: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="items")
    accounts: Mapped[list["Account"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"Item(plaid_item_id={self.plaid_item_id}, user_id={self.user_id})"
