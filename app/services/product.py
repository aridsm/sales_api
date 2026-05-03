from sqlalchemy.ext.asyncio import AsyncSession
from app.services.base import BaseService
from app.database.models.product import Product


class ProductService(BaseService[Product]):
    def __init__(self, session: AsyncSession):
        super().__init__(Product, session)
