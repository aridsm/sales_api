from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserOwnedService
from app.database.models.product import Product
from app.api.schemas.product import ProductCreate, ProductUpdate


class ProductService(UserOwnedService[Product, ProductCreate, ProductUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(Product, session)
