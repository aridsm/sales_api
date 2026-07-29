from typing import List
from uuid import UUID
from datetime import datetime
from app.enums.stock_entry import StockEntryStatus
from app.database.models.stock_entry import StockEntry
from app.database.models.stock_entry_product import StockEntryProduct
from app.database.models.product import Product
from fastapi import APIRouter, status, Query
from sqlalchemy import exists, select as sa_select, cast, String

from app.api.schemas.stock_entry import (
    StockEntryCreate,
    StockEntryResponse,
    StockEntryBulkDelete,
)
from app.api.dependencies import UserLoggedDep, StockEntryServiceDep
from app.api.utils.paginated_response import PaginatedResponse

router = APIRouter(prefix="/stock_entries", tags=["stock_entries"])


@router.get("/", response_model=PaginatedResponse[StockEntryResponse])
async def get_all_stock_entries(
    user: UserLoggedDep,
    service: StockEntryServiceDep,
    page: int = 1,
    page_size: int = 20,
    sort: str | None = "date",
    status: List[StockEntryStatus] | None = Query(None),
    id: List[UUID] | None = Query(None),
    search: str | None = None,
    start_total: float | None = Query(None),
    end_total: float | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    product_id: List[UUID] | None = Query(None),
    category_id: List[UUID] | None = Query(None),
):
    query = service.get_base_query(user_id=str(user.id))

    if search:
        query = query.where(cast(StockEntry.code, String).ilike(f"%{search}%"))

    if start_total is not None:
        query = query.where(StockEntry.total >= start_total)
    if end_total is not None:
        query = query.where(StockEntry.total <= end_total)
    if start_date:
        query = query.where(StockEntry.date >= start_date)
    if end_date:
        query = query.where(StockEntry.date <= end_date)

    if product_id:
        product_exists = exists(
            sa_select(StockEntryProduct.id)
            .where(
                StockEntryProduct.stock_entry_id == StockEntry.id,
                StockEntryProduct.product_id.in_(product_id),
            )
            .correlate(StockEntry)
        )
        query = query.where(product_exists)

    if category_id:
        category_exists = exists(
            sa_select(StockEntryProduct.id)
            .join(Product, StockEntryProduct.product_id == Product.id)
            .where(
                StockEntryProduct.stock_entry_id == StockEntry.id,
                Product.category_id.in_(category_id),
            )
            .correlate(StockEntry)
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


@router.get("/{id}", response_model=StockEntryResponse)
async def get_stock_entry_by_id(
    id: UUID,
    user: UserLoggedDep,
    service: StockEntryServiceDep,
):
    return await service.get_entry_with_details(id, str(user.id))


@router.post(
    "/", response_model=StockEntryResponse, status_code=status.HTTP_201_CREATED
)
async def create_stock_entry(
    body: StockEntryCreate,
    user: UserLoggedDep,
    service: StockEntryServiceDep,
):
    return await service.create_entry_with_products(body.products, body.date, user.id)


@router.post("/{id}/cancel", response_model=StockEntryResponse)
async def cancel_stock_entry(
    id: UUID,
    user: UserLoggedDep,
    service: StockEntryServiceDep,
):
    return await service.cancel_entry(id, user.id)


@router.delete("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bulk_stock_entries(
    body: StockEntryBulkDelete,
    user: UserLoggedDep,
    service: StockEntryServiceDep,
):
    await service.delete_bulk(body.ids, str(user.id))


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stock_entry(
    id: UUID,
    user: UserLoggedDep,
    service: StockEntryServiceDep,
):
    await service.delete(id, str(user.id))
