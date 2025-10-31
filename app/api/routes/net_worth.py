from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.schemas.analytics import NetWorthHistoryPoint, NetWorthResponse
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/v1/net-worth", tags=["analytics"])


@router.get("/", response_model=NetWorthResponse)
async def get_net_worth(
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    analytics = AnalyticsService(session)
    summary = await analytics.net_worth(str(current_user.id))
    history = await analytics.recent_net_worth(str(current_user.id))

    history_points = [
        NetWorthHistoryPoint(
            as_of_date=entry_date,
            net_worth=value,
        )
        for entry_date, value in history
    ]

    return NetWorthResponse(
        net_worth=summary.net_worth,
        assets=summary.assets,
        liabilities=summary.liabilities,
        history=history_points,
    )
