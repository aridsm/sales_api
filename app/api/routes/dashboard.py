from fastapi import APIRouter, Query
from app.api.dependencies import UserLoggedDep, DashboardServiceDep
from app.api.schemas.dashboard import ChartItem, FrequencyEnum, BudgetResponse
from datetime import datetime

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/chart", response_model=list[ChartItem])
async def get_chart_data(
    user: UserLoggedDep,
    service: DashboardServiceDep,
    frequency: FrequencyEnum = Query(FrequencyEnum.daily),
    count: int = Query(7, ge=1, le=100),
    previous: int = Query(0, ge=0),
    timezone_offset: int = Query(
        0, description="Timezone offset in minutes (e.g. 180 for UTC-3)"
    ),
):

    return await service.get_chart_data(
        company_id=str(user.company_id),
        frequency=frequency,
        count=count,
        previous=previous,
        timezone_offset=timezone_offset,
    )


@router.get("/budgets", response_model=BudgetResponse)
async def get_budgets(
    user: UserLoggedDep,
    service: DashboardServiceDep,
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
):
    return await service.get_budgets(
        company_id=str(user.company_id),
        start_date=start_date,
        end_date=end_date,
    )
