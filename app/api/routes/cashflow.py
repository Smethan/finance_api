from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.schemas.analytics import CashflowResponse
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/v1/cashflow", tags=["analytics"])


@router.get("/summary", response_model=CashflowResponse)
async def cashflow_summary(
    *,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    analytics = AnalyticsService(session)
    summary = await analytics.cashflow_summary(
        str(current_user.id),
        start_date=start_date,
        end_date=end_date,
    )

    net = summary.inflow - summary.outflow
    return CashflowResponse(
        start_date=summary.start_date,
        end_date=summary.end_date,
        inflow=summary.inflow,
        outflow=summary.outflow,
        net=net,
    )
