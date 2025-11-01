from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.schemas.base import APIModel


class ItemRead(APIModel):
    id: str
    plaid_item_id: str
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None
    webhook_status: Optional[str] = None
    cursor: Optional[str] = None
    last_successful_sync: Optional[datetime] = None
