from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.sync import SyncOrchestrator
from plaid.exceptions import ApiException


def test_fetch_investments_holdings_skips_when_product_not_enabled():
    session = AsyncMock(spec=AsyncSession)
    plaid_service = AsyncMock()
    orchestrator = SyncOrchestrator(session, plaid=plaid_service)

    error = ApiException(status=400, reason="PRODUCT_NOT_ENABLED")
    error.body = json.dumps(
        {
            "error_code": "PRODUCT_NOT_ENABLED",
            "error_message": "Investments product not enabled for this item",
        }
    )

    async def _raise(*args, **kwargs):
        raise error

    plaid_service.investments_holdings = AsyncMock(side_effect=_raise)

    payload = asyncio.run(orchestrator._fetch_investments_holdings("item-123", "token"))

    assert payload == {"securities": [], "holdings": []}
    plaid_service.investments_holdings.assert_awaited()


def test_fetch_investments_holdings_raises_for_unexpected_error():
    session = AsyncMock(spec=AsyncSession)
    plaid_service = AsyncMock()
    orchestrator = SyncOrchestrator(session, plaid=plaid_service)

    error = ApiException(status=500, reason="server error")
    error.body = json.dumps({"error_code": "INTERNAL_SERVER_ERROR"})

    async def _raise(*args, **kwargs):
        raise error

    plaid_service.investments_holdings = AsyncMock(side_effect=_raise)

    with pytest.raises(ApiException):
        asyncio.run(orchestrator._fetch_investments_holdings("item-123", "token"))
