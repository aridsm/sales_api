import uuid

from fastapi import APIRouter, status, Query

from app.api.schemas.sale_product import (
    SaleProductCreate,
    SaleProductResponse,
    SaleProductBulkDelete,
)
from app.api.dependencies import UserLoggedDep, SaleProductServiceDep
from app.api.utils.paginated_response import PaginatedResponse
from app.database.models.sale_product import SaleProduct

router = APIRouter(prefix="/sale_products", tags=["sale_products"])


@router.get("/", response_model=PaginatedResponse[SaleProductResponse])
async def get_all_sale_products(
    user: UserLoggedDep,
    service: SaleProductServiceDep,
    sale_id: uuid.UUID | None = None,
    product_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
):
    result = await service.get_all(
        user_id=str(user.id),
        page=page,
        page_size=page_size,
        sale_id=sale_id,
        product_id=product_id,
    )
    return result


@router.get("/{sale_product_id}", response_model=SaleProductResponse)
async def get_sale_product_by_id(
    sale_product_id: uuid.UUID,
    user: UserLoggedDep,
    service: SaleProductServiceDep,
):
    return await service.get_by_id(sale_product_id, str(user.id))


@router.post(
    "/", response_model=SaleProductResponse, status_code=status.HTTP_201_CREATED
)
async def create_sale_product(
    body: SaleProductCreate,
    user: UserLoggedDep,
    service: SaleProductServiceDep,
):
    return await service.create(SaleProduct(**body.model_dump()), user.id)


@router.delete("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bulk_sale_products(
    body: SaleProductBulkDelete,
    user: UserLoggedDep,
    service: SaleProductServiceDep,
):
    await service.delete_bulk(body.ids, str(user.id))


@router.delete("/{sale_product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sale_product(
    sale_product_id: uuid.UUID,
    user: UserLoggedDep,
    service: SaleProductServiceDep,
):
    await service.delete(sale_product_id, str(user.id))
