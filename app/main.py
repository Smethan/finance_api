from __future__ import annotations

from contextlib import asynccontextmanager

import sentry_sdk
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.logging import configure_logging
from app.core.settings import settings
from app.workers.sync_worker import run_full_sync

limiter = Limiter(key_func=get_remote_address)  # type: ignore[arg-type]
scheduler: AsyncIOScheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=str(settings.sentry_dsn), traces_sample_rate=0.1)

    global scheduler
    scheduler = AsyncIOScheduler(timezone=settings.scheduler.timezone)
    balance_trigger = CronTrigger.from_crontab(
        settings.scheduler.balance_refresh_cron,
        timezone=settings.scheduler.timezone,
    )
    scheduler.add_job(
        run_full_sync,
        trigger=balance_trigger,
        id="daily_balance_refresh",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.start()

    logger.info("Finance API started")
    try:
        yield
    finally:
        if scheduler:
            scheduler.shutdown(wait=False)
        logger.info("Finance API stopped")


app = FastAPI(
    title="Finance Aggregation API",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
        headers={"Retry-After": str(exc.detail)},
    )

if settings.api.allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

default_rate_limit = settings.api.rate_limit
if default_rate_limit:
    limiter.default_limits = [default_rate_limit]

app.add_middleware(SlowAPIMiddleware)

app.include_router(api_router)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response
