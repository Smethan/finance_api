from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", include_in_schema=False)
async def healthcheck():
    return {"status": "ok"}
