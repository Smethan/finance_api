from __future__ import annotations

from loguru import logger
from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.item import Item
from app.services.sync import SyncOrchestrator


async def run_full_sync() -> None:
    async with async_session_factory() as session:
        result = await session.execute(select(Item.id))
        item_ids = [str(row[0]) for row in result]

    for item_id in item_ids:
        async with async_session_factory() as session:
            item = await session.get(Item, item_id)
            if item is None:
                continue
            orchestrator = SyncOrchestrator(session)
            try:
                await orchestrator.run_item_sync(item)
                await session.commit()
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.exception("Failed to sync item {item_id}: {error}", item_id=item.id, error=exc)
