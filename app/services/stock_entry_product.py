from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy import Select
import uuid
from app.services.base import BaseService
from app.database.models.stock_entry_product import StockEntryProduct
from app.database.models.product import Product
from app.database.models.category import Category


class StockEntryProductService(BaseService[StockEntryProduct]):
    def __init__(self, session: AsyncSession):
        super().__init__(StockEntryProduct, session)

    def get_base_query(self, user_id: str) -> Select:
        return (
            select(
                StockEntryProduct,
                Product.name.label("product_name"),
                Category.name.label("category_name"),
                Category.color.label("category_color"),
            )
            .join(Product, Product.id == StockEntryProduct.product_id)
            .join(Category, Category.id == Product.category_id)
            .where(StockEntryProduct.user_id == user_id)
        )

    async def get_all(
        self, query: Select | None = None, user_id: str | None = None, **kwargs
    ):
        if query is None:
            query = self.get_base_query(user_id=user_id)
        return await super().get_all(query=query, user_id=user_id, **kwargs)
