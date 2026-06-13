from fastapi import APIRouter, Query
from app.api.dependencies import UserLoggedDep, DashboardServiceDep
from app.api.schemas.dashboard import ChartItem, FrequencyEnum

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
        user_id=str(user.id),
        frequency=frequency,
        count=count,
        previous=previous,
        timezone_offset=timezone_offset,
    )
