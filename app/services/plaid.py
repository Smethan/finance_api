from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import plaid
from plaid.api import plaid_api
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.transactions_sync_request import TransactionsSyncRequest

from app.core.settings import settings


PLAID_ENVIRONMENTS: dict[str, str] = {
    "sandbox": plaid.Environment.Sandbox,
    "development": plaid.Environment.Development,
    "production": plaid.Environment.Production,
}


@dataclass
class SyncResult:
    transactions: List[Dict[str, Any]]
    accounts: List[Dict[str, Any]]
    next_cursor: str
    has_more: bool


class PlaidService:
    def __init__(self) -> None:
        plaid_env = PLAID_ENVIRONMENTS.get(settings.plaid.environment.lower(), plaid.Environment.Sandbox)
        configuration = plaid.Configuration(
            host=plaid_env,
            api_key={
                "clientId": settings.plaid.client_id,
                "secret": settings.plaid.secret,
            },
        )
        self._api_client = plaid_api.PlaidApi(plaid.ApiClient(configuration))

    async def _call(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        method = getattr(self._api_client, method_name)
        return await asyncio.to_thread(method, *args, **kwargs)

    async def create_link_token(self, user_id: str, products: Optional[Iterable[str]] = None) -> str:
        request = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id=user_id),
            client_name="Personal Finance API",
            products=[Products(prod) for prod in (products or settings.plaid.products)],
            country_codes=[CountryCode(code) for code in settings.plaid.country_codes],
            redirect_uri=settings.plaid.redirect_uri,
            language="en",
        )
        response = await self._call("link_token_create", request)
        return response["link_token"]

    async def exchange_public_token(self, public_token: str) -> Dict[str, Any]:
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = await self._call("item_public_token_exchange", request)
        return {
            "access_token": response["access_token"],
            "item_id": response["item_id"],
        }

    async def transactions_sync(
        self,
        access_token: str,
        cursor: Optional[str] = None,
        count: int = 500,
    ) -> SyncResult:
        request = TransactionsSyncRequest(
            access_token=access_token,
            cursor=cursor,
            count=count,
        )
        response = await self._call("transactions_sync", request)
        added = response["added"]
        modified = response["modified"]
        removed = response["removed"]

        transactions: List[Dict[str, Any]] = []
        transactions.extend(added)
        transactions.extend(modified)
        # Removed transactions only include transaction ids; surface them for soft deletes.
        for removed_txn in removed:
            transactions.append(
                {
                    "transaction_id": removed_txn["transaction_id"],
                    "removed": True,
                }
            )

        return SyncResult(
            transactions=transactions,
            accounts=response.get("accounts", []),
            next_cursor=response["next_cursor"],
            has_more=response["has_more"],
        )

    async def accounts_balance(self, access_token: str) -> Dict[str, Any]:
        request = AccountsBalanceGetRequest(access_token=access_token)
        response = await self._call("accounts_balance_get", request)
        return response.to_dict()

    async def investments_holdings(self, access_token: str) -> Dict[str, Any]:
        request = InvestmentsHoldingsGetRequest(access_token=access_token)
        response = await self._call("investments_holdings_get", request)
        return response.to_dict()


plaid_service = PlaidService()
