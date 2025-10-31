from __future__ import annotations

from typing import Optional

from app.schemas.base import TimestampedModel


class UserRead(TimestampedModel):
    email: str
    external_id: Optional[str] = None
    profile: Optional[dict] = None
