from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Iterable, Sequence

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.balance_snapshot import BalanceSnapshot
from app.models.holding import Holding
from app.models.item import Item
from app.models.security import Security
from app.models.transaction import Transaction
from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(self, email: str, external_id: str | None = None) -> User:
        result = await self.session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            if external_id and user.external_id != external_id:
                user.external_id = external_id
            return user

        user = User(email=email, external_id=external_id)
        self.session.add(user)
        await self.session.flush()
        return user


class ItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(
        self,
        *,
        user_id: str,
        plaid_item_id: str,
        access_token_encrypted: str,
        institution_id: str | None,
        institution_name: str | None,
        webhook_status: str | None = None,
        cursor: str | None = None,
    ) -> Item:
        stmt = (
            insert(Item)
            .values(
                user_id=user_id,
                plaid_item_id=plaid_item_id,
                access_token_encrypted=access_token_encrypted,
                institution_id=institution_id,
                institution_name=institution_name,
                webhook_status=webhook_status,
                cursor=cursor,
            )
            .on_conflict_do_update(
                index_elements=[Item.plaid_item_id],
                set_={
                    "access_token_encrypted": access_token_encrypted,
                    "institution_id": institution_id,
                    "institution_name": institution_name,
                    "webhook_status": webhook_status,
                    "cursor": cursor,
                    "updated_at": datetime.utcnow(),
                },
            )
        ).returning(Item)
        result = await self.session.execute(stmt)
        item = result.scalar_one()
        await self.session.flush()
        return item

    async def update_cursor(
        self,
        *,
        item_id: str,
        cursor: str | None,
        last_successful_sync: datetime | None,
    ) -> None:
        stmt = (
            update(Item)
            .where(Item.id == item_id)
            .values(cursor=cursor, last_successful_sync=last_successful_sync)
        )
        await self.session.execute(stmt)

    async def get_by_id(self, item_id: str) -> Item | None:
        result = await self.session.execute(select(Item).where(Item.id == item_id))
        return result.scalar_one_or_none()


class AccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def bulk_upsert(self, accounts: Sequence[dict], item_id: str) -> None:
        for account_data in accounts:
            stmt = (
                insert(Account)
                .values(
                    item_id=item_id,
                    plaid_account_id=account_data["account_id"],
                    name=account_data.get("name"),
                    official_name=account_data.get("official_name"),
                    mask=account_data.get("mask"),
                    type=account_data.get("type"),
                    subtype=account_data.get("subtype"),
                    verification_status=account_data.get("verification_status"),
                    iso_currency_code=account_data.get("balances", {}).get("iso_currency_code"),
                    current_balance=self._decimal(account_data.get("balances", {}).get("current")),
                    available_balance=self._decimal(account_data.get("balances", {}).get("available")),
                    limit=self._decimal(account_data.get("balances", {}).get("limit")),
                )
                .on_conflict_do_update(
                    index_elements=[Account.plaid_account_id],
                    set_={
                        "name": account_data.get("name"),
                        "official_name": account_data.get("official_name"),
                        "mask": account_data.get("mask"),
                        "type": account_data.get("type"),
                        "subtype": account_data.get("subtype"),
                        "verification_status": account_data.get("verification_status"),
                        "iso_currency_code": account_data.get("balances", {}).get("iso_currency_code"),
                        "current_balance": self._decimal(
                            account_data.get("balances", {}).get("current")
                        ),
                        "available_balance": self._decimal(
                            account_data.get("balances", {}).get("available")
                        ),
                        "limit": self._decimal(account_data.get("balances", {}).get("limit")),
                    },
                )
            )
            await self.session.execute(stmt)

    @staticmethod
    def _decimal(value: float | Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return Decimal(str(value))


class TransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def bulk_upsert(self, transactions: Sequence[dict], plaid_account_id_map: dict[str, str]) -> None:
        for txn in transactions:
            if txn.get("removed"):
                await self._mark_removed(txn, plaid_account_id_map)
                continue
            account_id = plaid_account_id_map.get(txn["account_id"])
            if not account_id:
                continue
            amount = self._signed_amount(txn)
            stmt = (
                insert(Transaction)
                .values(
                    account_id=account_id,
                    plaid_transaction_id=txn["transaction_id"],
                    transaction_id=txn.get("transaction_id"),
                    transaction_code=txn.get("transaction_code"),
                    name=txn.get("name"),
                    merchant_name=txn.get("merchant_name"),
                    transaction_type=txn.get("transaction_type"),
                    amount=amount,
                    iso_currency_code=txn.get("iso_currency_code"),
                    date=self._parse_date(txn.get("date")),
                    authorized_date=self._parse_date(txn.get("authorized_date")),
                    pending=txn.get("pending", False),
                    payment_channel=txn.get("payment_channel"),
                    personal_finance_category=txn.get("personal_finance_category"),
                    category=txn.get("category"),
                    counterparty=txn.get("counterparty"),
                    last_modified_at=self._parse_datetime(txn.get("datetime")),
                )
                .on_conflict_do_update(
                    index_elements=[Transaction.plaid_transaction_id],
                    set_={
                        "transaction_code": txn.get("transaction_code"),
                        "name": txn.get("name"),
                        "merchant_name": txn.get("merchant_name"),
                        "transaction_type": txn.get("transaction_type"),
                        "amount": amount,
                        "iso_currency_code": txn.get("iso_currency_code"),
                        "date": self._parse_date(txn.get("date")),
                        "authorized_date": self._parse_date(txn.get("authorized_date")),
                        "pending": txn.get("pending", False),
                        "payment_channel": txn.get("payment_channel"),
                        "personal_finance_category": txn.get("personal_finance_category"),
                        "category": txn.get("category"),
                        "counterparty": txn.get("counterparty"),
                        "last_modified_at": self._parse_datetime(txn.get("datetime")),
                    },
                )
            )
            await self.session.execute(stmt)

    async def _mark_removed(self, transaction: dict, plaid_account_id_map: dict[str, str]) -> None:
        transaction_id = transaction.get("transaction_id")
        if not transaction_id:
            return
        stmt = (
            update(Transaction)
            .where(Transaction.plaid_transaction_id == transaction_id)
            .values(pending=False)
        )
        await self.session.execute(stmt)

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None
        return date.fromisoformat(value)

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _signed_amount(transaction: dict) -> Decimal:
        raw = Decimal(str(transaction.get("amount", 0)))
        tx_type = (transaction.get("transaction_type") or "").lower()
        if tx_type == "credit":
            return raw * Decimal("-1")
        return raw


class SecurityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def bulk_upsert(self, securities: Sequence[dict]) -> dict[str, str]:
        security_ids: dict[str, str] = {}
        for security in securities:
            stmt = (
                insert(Security)
                .values(
                    plaid_security_id=security["security_id"],
                    name=security.get("name"),
                    ticker_symbol=security.get("ticker_symbol"),
                    isin=security.get("isin"),
                    cusip=security.get("cusip"),
                    type=security.get("type"),
                    close_price=security.get("close_price"),
                    close_price_date=security.get("close_price_date"),
                    currency=security.get("iso_currency_code"),
                )
                .on_conflict_do_update(
                    index_elements=[Security.plaid_security_id],
                    set_={
                        "name": security.get("name"),
                        "ticker_symbol": security.get("ticker_symbol"),
                        "isin": security.get("isin"),
                        "cusip": security.get("cusip"),
                        "type": security.get("type"),
                        "close_price": security.get("close_price"),
                        "close_price_date": security.get("close_price_date"),
                        "currency": security.get("iso_currency_code"),
                    },
                )
                .returning(Security.id, Security.plaid_security_id)
            )
            result = await self.session.execute(stmt)
            sec_row = result.one()
            mapping = sec_row._mapping
            security_ids[mapping[Security.plaid_security_id]] = str(mapping[Security.id])
        return security_ids


class HoldingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def bulk_upsert(
        self,
        holdings: Sequence[dict],
        plaid_account_id_map: dict[str, str],
        plaid_security_id_map: dict[str, str],
    ) -> None:
        for holding in holdings:
            account_id = plaid_account_id_map.get(holding.get("account_id"))
            security_id = plaid_security_id_map.get(holding.get("security_id"))
            if not account_id or not security_id:
                continue
            stmt = (
                insert(Holding)
                .values(
                    account_id=account_id,
                    security_id=security_id,
                    quantity=holding.get("quantity"),
                    institution_value=holding.get("institution_value"),
                    institution_price=holding.get("institution_price"),
                    institution_price_as_of=holding.get("institution_price_as_of"),
                    cost_basis=holding.get("cost_basis"),
                    last_updated=holding.get("last_updated"),
                )
                .on_conflict_do_update(
                    index_elements=[Holding.account_id, Holding.security_id],
                    set_={
                        "quantity": holding.get("quantity"),
                        "institution_value": holding.get("institution_value"),
                        "institution_price": holding.get("institution_price"),
                        "institution_price_as_of": holding.get("institution_price_as_of"),
                        "cost_basis": holding.get("cost_basis"),
                        "last_updated": holding.get("last_updated"),
                    },
                )
            )
            await self.session.execute(stmt)


class BalanceSnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_snapshot(
        self,
        *,
        user_id: str,
        as_of_date: date,
        net_worth: Decimal | None,
        liquid_assets: Decimal | None,
        investments: Decimal | None,
        liabilities: Decimal | None,
        cash_flow_in: Decimal | None,
        cash_flow_out: Decimal | None,
    ) -> None:
        stmt = (
            insert(BalanceSnapshot)
            .values(
                user_id=user_id,
                as_of_date=as_of_date,
                net_worth=net_worth,
                liquid_assets=liquid_assets,
                investments=investments,
                liabilities=liabilities,
                cash_flow_in=cash_flow_in,
                cash_flow_out=cash_flow_out,
            )
            .on_conflict_do_update(
                index_elements=[BalanceSnapshot.user_id, BalanceSnapshot.as_of_date],
                set_={
                    "net_worth": net_worth,
                    "liquid_assets": liquid_assets,
                    "investments": investments,
                    "liabilities": liabilities,
                    "cash_flow_in": cash_flow_in,
                    "cash_flow_out": cash_flow_out,
                },
            )
        )
        await self.session.execute(stmt)
