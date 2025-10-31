from __future__ import annotations

import uuid
from typing import List

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(128), index=True)
    profile: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    items: Mapped[List["Item"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!s}, email={self.email})"
