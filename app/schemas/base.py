from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, arbitrary_types_allowed=True)


class TimestampedModel(APIModel):
    id: str
    created_at: datetime
    updated_at: datetime
