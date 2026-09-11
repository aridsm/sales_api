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
    CanViewDep,
    ProductServiceDep,
    CanEditDep,
)
from app.api.utils.paginated_response import PaginatedResponse
from app.database.models.category import Category
from app.database.models.product import Product
from app.database.models.user import User

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=PaginatedResponse[ProductResponse])
async def get_all_products(
    user: CanViewDep,
    service: ProductServiceDep,
    category_id: list[UUID] | None = Query(default=None),
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    start_price: float | None = Query(None),
    end_price: float | None = Query(None),
    start_created_at: datetime | None = Query(None),
    end_created_at: datetime | None = Query(None),
    start_stock_amount: int | None = Query(None),
    end_stock_amount: int | None = Query(None),
):

    query = (
        select(
            Product,
            Category.name.label("category_name"),
            Category.color.label("category_color"),
            User.name.label("created_by_name"),
            User.email.label("created_by_email"),
        )
        .outerjoin(Category, Product.category_id == Category.id)
        .outerjoin(User, Product.created_by == User.id)
    )

    if start_price is not None:
        query = query.where(Product.price >= start_price)
    if end_price is not None:
        query = query.where(Product.price <= end_price)
    if start_created_at:
        query = query.where(Product.created_at >= start_created_at)
    if end_created_at:
        query = query.where(Product.created_at <= end_created_at)
    if start_stock_amount is not None:
        query = query.where(Product.stock_amount >= start_stock_amount)
    if end_stock_amount is not None:
        query = query.where(Product.stock_amount <= end_stock_amount)

    result = await service.get_all(
        query=query,
        company_id=user.company_id,
        page=page,
        page_size=page_size,
        search=search,
        category_id=category_id,
    )
    return result


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product_by_id(
    product_id: uuid.UUID,
    user: CanViewDep,
    service: ProductServiceDep,
):
    query = (
        select(
            Product,
            Category.name.label("category_name"),
            Category.color.label("category_color"),
            User.name.label("created_by_name"),
            User.email.label("created_by_email"),
        )
        .outerjoin(Category, Product.category_id == Category.id)
        .outerjoin(User, Product.created_by == User.id)
        .where(Product.id == product_id)
    )
    return await service.get_by_id(product_id, company_id=user.company_id, query=query)


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    user: CanEditDep,
    service: ProductServiceDep,
):
    return await service.create(
        Product(user_id=user.id, created_by=user.id, company_id=user.company_id, **body.model_dump()),
        user_id=user.id,
        company_id=user.company_id,
    )


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    body: ProductUpdate,
    user: CanEditDep,
    service: ProductServiceDep,
):
    return await service.update(
        product_id, body, company_id=user.company_id, user_id=user.id
    )


@router.delete("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bulk_products(
    body: ProductBulkDelete,
    user: CanEditDep,
    service: ProductServiceDep,
):
    await service.delete_bulk(
        body.ids, company_id=str(user.company_id), user_id=user.id
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    user: CanEditDep,
    service: ProductServiceDep,
):
    await service.delete(product_id, company_id=str(user.company_id), user_id=user.id)
