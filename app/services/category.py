from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.base import BaseService
from app.database.models.category import Category
from app.database.models.product import Product


class CategoryService(BaseService[Category]):
    def __init__(self, session: AsyncSession):
        super().__init__(Category, session)

    def get_base_query_with_count(self, user_id: str):
        return (
            select(Category, func.count(Product.id).label("products"))
            .outerjoin(Product, Category.id == Product.category_id)
            .where(Category.user_id == user_id)
            .group_by(Category.id)
        )

