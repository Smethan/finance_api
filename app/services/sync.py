from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_string
from app.models.account import Account
from app.models.item import Item
from app.services.analytics import AnalyticsService
from app.services.plaid import PlaidService, SyncResult, plaid_service
from app.services.repositories import (
    AccountRepository,
    BalanceSnapshotRepository,
    HoldingRepository,
    ItemRepository,
    SecurityRepository,
    TransactionRepository,
)


@dataclass
class SyncOutcome:
    item_id: str
    transactions_synced: int
    holdings_synced: int
    cursor: str | None


class SyncOrchestrator:
    def __init__(self, session: AsyncSession, plaid: PlaidService | None = None) -> None:
        self.session = session
        self.plaid = plaid or plaid_service
        self.items = ItemRepository(session)
        self.accounts = AccountRepository(session)
        self.transactions = TransactionRepository(session)
        self.securities = SecurityRepository(session)
        self.holdings = HoldingRepository(session)
        self.balance_snapshots = BalanceSnapshotRepository(session)
        self.analytics = AnalyticsService(session)

    async def run_item_sync(self, item: Item) -> SyncOutcome:
        access_token = decrypt_string(item.access_token_encrypted)
        cursor = item.cursor

        accounts_payload = await self.plaid.accounts_balance(access_token)
        await self.accounts.bulk_upsert(accounts_payload["accounts"], str(item.id))
        account_map = await self._account_map(item.id)

        total_transactions = 0
        has_more = True
        latest_cursor = cursor

        while has_more:
            sync_result = await self._sync_transactions(access_token=access_token, cursor=latest_cursor)
            await self._persist_transactions(item, sync_result, account_map)
            latest_cursor = sync_result.next_cursor
            has_more = sync_result.has_more
            total_transactions += len(sync_result.transactions)

        holdings_payload = await self.plaid.investments_holdings(access_token)
        security_map = await self.securities.bulk_upsert(holdings_payload["securities"])
        await self.holdings.bulk_upsert(
            holdings_payload["holdings"],
            plaid_account_id_map=account_map,
            plaid_security_id_map=security_map,
        )

        await self.items.update_cursor(
            item_id=str(item.id),
            cursor=latest_cursor or cursor,
            last_successful_sync=datetime.now(timezone.utc),
        )

        net_worth = await self.analytics.net_worth(str(item.user_id))
        await self.balance_snapshots.upsert_snapshot(
            user_id=str(item.user_id),
            as_of_date=datetime.now(timezone.utc).date(),
            net_worth=net_worth.net_worth,
            liquid_assets=net_worth.assets,
            investments=None,
            liabilities=net_worth.liabilities,
            cash_flow_in=None,
            cash_flow_out=None,
        )

        return SyncOutcome(
            item_id=str(item.id),
            transactions_synced=total_transactions,
            holdings_synced=len(holdings_payload["holdings"]),
            cursor=latest_cursor,
        )

    async def _sync_transactions(self, access_token: str, cursor: str | None) -> SyncResult:
        return await self.plaid.transactions_sync(access_token, cursor)

    async def _persist_transactions(
        self,
        item: Item,
        sync_result: SyncResult,
        account_map: Dict[str, str],
    ) -> None:
        if sync_result.accounts:
            await self.accounts.bulk_upsert(sync_result.accounts, str(item.id))
        if sync_result.accounts:
            account_map.clear()
            account_map.update(await self._account_map(item.id))
        await self.transactions.bulk_upsert(sync_result.transactions, plaid_account_id_map=account_map)

    async def _account_map(self, item_id: str) -> Dict[str, str]:
        stmt = select(Account.plaid_account_id, Account.id).where(Account.item_id == item_id)
        result = await self.session.execute(stmt)
        return {row.plaid_account_id: str(row.id) for row in result}
