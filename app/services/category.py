from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserOwnedService
from app.database.models.category import Category
from app.api.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService(UserOwnedService[Category, CategoryCreate, CategoryUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(Category, session)
