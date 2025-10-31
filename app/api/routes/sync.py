from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.item import Item
from app.services.sync import SyncOrchestrator

router = APIRouter(prefix="/v1/sync", tags=["sync"])


class SyncTriggerRequest(BaseModel):
    item_id: str


@router.post("/trigger")
async def trigger_sync(
    payload: SyncTriggerRequest,
    background: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    item = await session.get(Item, payload.item_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    orchestrator = SyncOrchestrator(session)
    # Run synchronously for now; background tasks require independent session handling.
    result = await orchestrator.run_item_sync(item)
    return {"status": "ok", "synced_transactions": result.transactions_synced}


class PlaidWebhook(BaseModel):
    webhook_type: str
    webhook_code: str
    item_id: str


@router.post("/plaid/webhook", include_in_schema=False)
async def plaid_webhook(
    payload: PlaidWebhook,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    stmt = select(Item).where(Item.plaid_item_id == payload.item_id)
    item_result = await session.execute(stmt)
    item = item_result.scalar_one_or_none()
    if not item:
        return {"status": "ignored"}

    if payload.webhook_type == "TRANSACTIONS":
        orchestrator = SyncOrchestrator(session)
        await orchestrator.run_item_sync(item)
        return {"status": "synced"}

    return {"status": "ignored"}
