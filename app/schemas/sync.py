from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import Field

from app.schemas.base import APIModel


class SyncStatus(APIModel):
    item_id: str
    status: Literal["idle", "running", "error"] = "idle"
    cursor: Optional[str] = None
    last_successful_sync: Optional[datetime] = None
    message: Optional[str] = Field(default=None, description="Optional detail about the sync state.")
