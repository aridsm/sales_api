from typing import List
from uuid import UUID
from datetime import datetime
from app.enums.sale import SaleStatus
from app.database.models.sale import Sale
from app.database.models.sale_product import SaleProduct
from app.database.models.product import Product
from fastapi import APIRouter, status, Query
from sqlalchemy import cast, String, exists, select as sa_select

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
    sort: str | None = "created_at",
    status: List[SaleStatus] | None = Query(None),
    id: List[UUID] | None = Query(None),
    search: str | None = None,
    start_total: float | None = Query(None),
    end_total: float | None = Query(None),
    start_created_at: datetime | None = Query(None),
    end_created_at: datetime | None = Query(None),
    product_id: List[UUID] | None = Query(None),
    category_id: List[UUID] | None = Query(None),
):
    query = service.get_base_query(user_id=str(user.id))

    if search:
        query = query.where(cast(Sale.code, String).ilike(f"%{search}%"))

    if start_total is not None:
        query = query.where(Sale.total >= start_total)
    if end_total is not None:
        query = query.where(Sale.total <= end_total)
    if start_created_at:
        query = query.where(Sale.created_at >= start_created_at)
    if end_created_at:
        query = query.where(Sale.created_at <= end_created_at)

    if product_id:
        product_exists = exists(
            sa_select(SaleProduct.id)
            .where(
                SaleProduct.sale_id == Sale.id,
                SaleProduct.product_id.in_(product_id),
            )
            .correlate(Sale)
        )
        query = query.where(product_exists)

    if category_id:
        category_exists = exists(
            sa_select(SaleProduct.id)
            .join(Product, SaleProduct.product_id == Product.id)
            .where(
                SaleProduct.sale_id == Sale.id,
                Product.category_id.in_(category_id),
            )
            .correlate(Sale)
        )
        query = query.where(category_exists)

    result = await service.get_all(
        query=query,
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
