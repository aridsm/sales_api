from typing import List, Literal
from uuid import UUID
from app.database.models.category import Category
from app.database.models.product import Product
from app.enums.category import CategoryType
from fastapi import APIRouter, status, Query
from sqlalchemy import exists, select as sa_select
from app.api.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CategoryBulkDelete,
    CategoryAmountsWrapper,
)
from app.api.dependencies import UserLoggedDep, CategoryServiceDep, CanEditDep
from app.api.utils.paginated_response import PaginatedResponse
from datetime import datetime

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=PaginatedResponse[CategoryResponse])
async def get_all_categories(
    user: UserLoggedDep,
    service: CategoryServiceDep,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    sort: str | None = "created_at",
    type: List[CategoryType] | None = Query(None),
    id: List[UUID] | None = Query(None),
    include_ids: list[UUID] | None = Query(None),
    exclude_ids: list[UUID] | None = Query(None),
    get_all: bool = False,
    product_search: str | None = Query(None),
    start_product_created_at: datetime | None = Query(None),
    end_product_created_at: datetime | None = Query(None),
    start_price: float | None = Query(None),
    end_price: float | None = Query(None),
):
    base_query = service.get_base_query_with_count(str(user.company_id))

    if product_search:
        product_exists = exists(
            sa_select(Product.id)
            .where(
                Product.category_id == Category.id,
                Product.name.ilike(f"%{product_search}%"),
            )
            .correlate(Category)
        )
        base_query = base_query.where(product_exists)

    if (
        start_product_created_at
        or end_product_created_at
        or start_price is not None
        or end_price is not None
    ):
        product_conditions = [Product.category_id == Category.id]
        if start_product_created_at:
            product_conditions.append(Product.created_at >= start_product_created_at)
        if end_product_created_at:
            product_conditions.append(Product.created_at <= end_product_created_at)
        if start_price is not None:
            product_conditions.append(Product.price >= start_price)
        if end_price is not None:
            product_conditions.append(Product.price <= end_price)
        product_filter_exists = exists(
            sa_select(Product.id).where(*product_conditions).correlate(Category)
        )
        base_query = base_query.where(product_filter_exists)

    result = await service.get_all(
        company_id=str(user.company_id),
        query=base_query,
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        type=type,
        id=id,
        include_ids=include_ids,
        exclude_ids=exclude_ids,
        get_all=get_all,
    )
    return result


@router.get("/amounts", response_model=CategoryAmountsWrapper)
async def get_categories_amounts(
    user: UserLoggedDep,
    service: CategoryServiceDep,
    type: Literal["sales", "stock_entries", "other_expenses"] = Query("sales"),
    start_created_at: datetime | None = Query(None),
    end_created_at: datetime | None = Query(None),
):
    return await service.get_amounts(
        str(user.company_id),
        type=type,
        start_created_at=start_created_at,
        end_created_at=end_created_at,
    )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category_by_id(
    category_id: UUID,
    user: UserLoggedDep,
    service: CategoryServiceDep,
):
    return await service.get_by_id(category_id, company_id=str(user.company_id))


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    body: CategoryCreate,
    user: CanEditDep,
    service: CategoryServiceDep,
):
    return await service.create(
        Category(**body.model_dump(), user_id=user.id, company_id=user.company_id),
        user_id=user.id,
        company_id=user.company_id,
    )


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    body: CategoryUpdate,
    user: CanEditDep,
    service: CategoryServiceDep,
):
    return await service.update(category_id, body, company_id=user.company_id)


@router.delete("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bulk_categories(
    body: CategoryBulkDelete,
    user: CanEditDep,
    service: CategoryServiceDep,
):
    await service.delete_bulk(body.ids, company_id=str(user.company_id))


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    user: CanEditDep,
    service: CategoryServiceDep,
):
    await service.delete(category_id, company_id=str(user.company_id))
