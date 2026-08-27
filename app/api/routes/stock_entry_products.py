import uuid

from fastapi import APIRouter, status
from app.api.schemas.stock_entry_product import (
    StockEntryProductResponse,
    StockEntryProductBulkDelete,
)
from app.api.dependencies import UserLoggedDep, CanEditDep, StockEntryProductServiceDep
from app.api.utils.paginated_response import PaginatedResponse

router = APIRouter(prefix="/stock_entry_products", tags=["stock_entry_products"])


@router.get("/", response_model=PaginatedResponse[StockEntryProductResponse])
async def get_all_stock_entry_products(
    user: UserLoggedDep,
    service: StockEntryProductServiceDep,
    stock_entry_id: uuid.UUID | None = None,
    product_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
):
    result = await service.get_all(
        company_id=str(user.company_id),
        page=page,
        page_size=page_size,
        stock_entry_id=stock_entry_id,
        product_id=product_id,
    )
    return result


@router.get("/{id}", response_model=StockEntryProductResponse)
async def get_stock_entry_product_by_id(
    id: uuid.UUID,
    user: UserLoggedDep,
    service: StockEntryProductServiceDep,
):
    return await service.get_by_id(id, company_id=str(user.company_id))


@router.delete("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bulk_stock_entry_products(
    body: StockEntryProductBulkDelete,
    user: CanEditDep,
    service: StockEntryProductServiceDep,
):
    await service.delete_bulk(body.ids, company_id=str(user.company_id))


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stock_entry_product(
    id: uuid.UUID,
    user: CanEditDep,
    service: StockEntryProductServiceDep,
):
    await service.delete(id, company_id=str(user.company_id))
