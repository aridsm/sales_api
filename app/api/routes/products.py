import uuid
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, status, Query
from sqlmodel import select
from app.api.schemas.product import (
    ProductBulkDelete,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from app.api.dependencies import (
    UserLoggedDep,
    ProductServiceDep,
)
from app.api.utils.paginated_response import PaginatedResponse
from app.database.models.category import Category
from app.database.models.product import Product

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=PaginatedResponse[ProductResponse])
async def get_all_products(
    user: UserLoggedDep,
    service: ProductServiceDep,
    category_id: list[UUID] | None = Query(default=None),
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    start_price: float | None = Query(None),
    end_price: float | None = Query(None),
    start_created_at: datetime | None = Query(None),
    end_created_at: datetime | None = Query(None),
):

    query = select(
        Product,
        Category.name.label("category_name"),
        Category.color.label("category_color"),
    ).outerjoin(Category, Product.category_id == Category.id)

    if start_price is not None:
        query = query.where(Product.price >= start_price)
    if end_price is not None:
        query = query.where(Product.price <= end_price)
    if start_created_at:
        query = query.where(Product.created_at >= start_created_at)
    if end_created_at:
        query = query.where(Product.created_at <= end_created_at)

    result = await service.get_all(
        query=query,
        user_id=str(user.id),
        page=page,
        page_size=page_size,
        search=search,
        category_id=category_id,
    )
    return result


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product_by_id(
    product_id: uuid.UUID,
    user: UserLoggedDep,
    service: ProductServiceDep,
):
    return await service.get_by_id(product_id, str(user.id))


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    user: UserLoggedDep,
    service: ProductServiceDep,
):
    return await service.create(Product(user_id=user.id, **body.model_dump()), user.id)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    body: ProductUpdate,
    user: UserLoggedDep,
    service: ProductServiceDep,
):
    return await service.update(product_id, body, user.id)


@router.delete("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bulk_products(
    body: ProductBulkDelete,
    user: UserLoggedDep,
    service: ProductServiceDep,
):
    await service.delete_bulk(body.ids, str(user.id))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    user: UserLoggedDep,
    service: ProductServiceDep,
):
    await service.delete(product_id, str(user.id))
