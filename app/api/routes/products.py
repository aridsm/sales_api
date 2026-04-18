from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from app.api.schemas.product import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from app.api.dependencies import (
    UserLoggedDep,
    ProductServiceDep,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=list[ProductResponse])
async def get_all_products(
    user: UserLoggedDep,
    service: ProductServiceDep,
    page: int = 1,
    page_size: int = 20,
):
    result = await service.get_all_for_user(
        user_id=user.id, page=page, page_size=page_size
    )
    return result.items


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product_by_id(
    product_id: UUID,
    user: UserLoggedDep,
    service: ProductServiceDep,
):
    return await service.get_by_id_for_user(str(product_id), str(user.id))


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    user: UserLoggedDep,
    service: ProductServiceDep,
):
    return await service.create_for_user(body, str(user.id))


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    body: ProductUpdate,
    user: UserLoggedDep,
    service: ProductServiceDep,
):
    return await service.update_for_user(str(product_id), body, str(user.id))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    user: UserLoggedDep,
    service: ProductServiceDep,
):
    await service.delete_for_user(str(product_id), str(user.id))
