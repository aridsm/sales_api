from fastapi import APIRouter, status, Query
from typing import List
from datetime import datetime
from app.api.schemas.history import HistoryResponse, HistoryBulkDelete
from app.api.dependencies import UserLoggedDep, HistoryServiceDep
from app.api.utils.paginated_response import PaginatedResponse
from app.enums.history import ActionType, EntityType

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/", response_model=PaginatedResponse[HistoryResponse])
async def get_history(
    user: UserLoggedDep,
    service: HistoryServiceDep,
    page: int = 1,
    page_size: int = 20,
    search: str | None = Query(None),
    action_type: List[ActionType] | None = Query(None),
    entity_type: List[EntityType] | None = Query(None),
    start_created_at: datetime | None = Query(None),
    end_created_at: datetime | None = Query(None),
):
    return await service.get_recent_history(
        str(user.id), 
        page, 
        page_size, 
        search=search,
        action_type=action_type, 
        entity_type=entity_type,
        start_created_at=start_created_at,
        end_created_at=end_created_at,
    )

@router.delete("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bulk_history(
    body: HistoryBulkDelete,
    user: UserLoggedDep,
    service: HistoryServiceDep,
):
    await service.delete_bulk(body.ids, str(user.id))
