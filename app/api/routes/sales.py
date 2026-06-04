from typing import List
from uuid import UUID
from app.enums.sale import SaleStatus
from fastapi import APIRouter, status, Query

from app.api.schemas.sale import (
    SaleCreate,
    SaleResponse,
    SaleBulkDelete,
)
from app.api.dependencies import UserLoggedDep, SaleServiceDep
from app.api.utils.paginated_response import PaginatedResponse

router = APIRouter(prefix="/sales", tags=["sales"])


@router.get("/", response_model=PaginatedResponse[SaleResponse])
async def get_all_sales(
    user: UserLoggedDep,
    service: SaleServiceDep,
    page: int = 1,
    page_size: int = 20,
    sort: str | None = "category_id",
    status: List[SaleStatus] | None = Query(None),
    id: List[UUID] | None = Query(None),
):

    result = await service.get_all(
        user_id=str(user.id),
        page=page,
        page_size=page_size,
        sort=sort,
        status=status,
        id=id,
    )
    return result


@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale_by_id(
    sale_id: UUID,
    user: UserLoggedDep,
    service: SaleServiceDep,
):
    return await service.get_sale_with_details(sale_id, str(user.id))


@router.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
    body: SaleCreate,
    user: UserLoggedDep,
    service: SaleServiceDep,
):
    return await service.create_sale_with_products(body.products, user.id)


@router.post("/{sale_id}/cancel", response_model=SaleResponse)
async def cancel_sale(
    sale_id: UUID,
    user: UserLoggedDep,
    service: SaleServiceDep,
):
    return await service.cancel_sale(sale_id, user.id)


@router.delete("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bulk_sales(
    body: SaleBulkDelete,
    user: UserLoggedDep,
    service: SaleServiceDep,
):
    await service.delete_bulk(body.ids, str(user.id))


@router.delete("/{sale_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sale(
    sale_id: UUID,
    user: UserLoggedDep,
    service: SaleServiceDep,
):
    await service.delete(sale_id, str(user.id))
