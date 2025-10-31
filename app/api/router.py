from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    accounts,
    auth,
    cashflow,
    health,
    holdings,
    net_worth,
    plaid,
    sync,
    transactions,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(accounts.router)
api_router.include_router(transactions.router)
api_router.include_router(holdings.router)
api_router.include_router(net_worth.router)
api_router.include_router(cashflow.router)
api_router.include_router(sync.router)
api_router.include_router(plaid.router)
