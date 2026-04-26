from typing import List
from uuid import UUID
from app.enums.category import CategoryType
from fastapi import APIRouter, status, Query

from app.api.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CategoryBulkDelete,
)
from app.api.dependencies import UserLoggedDep, CategoryServiceDep
from app.api.utils.paginated_response import PaginatedResponse

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=PaginatedResponse[CategoryResponse])
async def get_all_categories(
    user: UserLoggedDep,
    service: CategoryServiceDep,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    sort: str | None = None,
    type: List[CategoryType] | None = Query(None),
):
    result = await service.get_all_for_user(
        user_id=str(user.id),
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        type=type,
    )
    return result


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category_by_id(
    category_id: UUID,
    user: UserLoggedDep,
    service: CategoryServiceDep,
):
    return await service.get_by_id_for_user(str(category_id), str(user.id))


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    body: CategoryCreate,
    user: UserLoggedDep,
    service: CategoryServiceDep,
):
    return await service.create_for_user(body, str(user.id))


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    body: CategoryUpdate,
    user: UserLoggedDep,
    service: CategoryServiceDep,
):
    return await service.update_for_user(str(category_id), body, str(user.id))


@router.delete("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bulk_categories(
    body: CategoryBulkDelete,
    user: UserLoggedDep,
    service: CategoryServiceDep,
):
    await service.delete_bulk_for_user(body.ids, str(user.id))


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    user: UserLoggedDep,
    service: CategoryServiceDep,
):
    await service.delete_for_user(str(category_id), str(user.id))
