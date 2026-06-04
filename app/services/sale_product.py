from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy import Select
import uuid
from typing import Any

from app.services.base import BaseService
from app.database.models.sale_product import SaleProduct
from app.database.models.product import Product
from app.database.models.category import Category


class SaleProductService(BaseService[SaleProduct]):
    def __init__(self, session: AsyncSession):
        super().__init__(SaleProduct, session)

    def _get_base_query(self) -> Select:
        return select(
            SaleProduct,
            Product.name.label("product_name"),
            Product.category_id.label("category_id"),
            Category.name.label("category_name"),
            Category.color.label("category_color"),
        ).join(Product, SaleProduct.product_id == Product.id).outerjoin(Category, Product.category_id == Category.id)

    async def get_all(
        self,
        query: Select | None = None,
        **kwargs
    ):
        if query is None:
            query = self._get_base_query()
        return await super().get_all(query=query, **kwargs)

    async def get_by_id(
        self, 
        id: uuid.UUID, 
        user_id: uuid.UUID | str | None = None, 
        query: Select | None = None
    ) -> Any:
        if query is None:
            query = self._get_base_query().where(SaleProduct.id == id)
        return await super().get_by_id(id, user_id=user_id, query=query)

    async def create(self, item: SaleProduct, user_id: uuid.UUID | None = None) -> Any:
        created_item = await super().create(item, user_id=user_id)
        return await self.get_by_id(created_item.id, user_id=user_id)
