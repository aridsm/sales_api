import uuid

from fastapi import APIRouter, status, Query
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
from app.database.models.product import Product

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=PaginatedResponse[ProductResponse])
async def get_all_products(
    user: UserLoggedDep,
    service: ProductServiceDep,
    category_id: list[str] | None = Query(default=None),
    page: int = 1,
    page_size: int = 20,
):
    if category_id:
        category_id = [c for c in category_id if c]
        if not category_id:
            category_id = None
            
    result = await service.get_all(
        user_id=str(user.id), 
        page=page, 
        page_size=page_size, 
        category_id=category_id
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
async def delete_bulk_categories(
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
