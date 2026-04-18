from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.services.base import BaseService
from app.database.models.category import Category
from app.api.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService(BaseService[Category]):
    def __init__(self, session: AsyncSession):
        super().__init__(Category, session)

    async def get_all_for_user(
        self,
        user_id: str,
        page_size: int = 20,
        page: int = 1,
        get_all=False,
    ):
        query = select(self.model).where(self.model.user_id == user_id)
        return await self.get_all(
            query=query, page_size=page_size, page=page, get_all=get_all
        )

    async def get_by_id_for_user(self, id: str, user_id: str) -> Optional[Category]:
        category = await self.get_by_id(id)
        if category.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="errorAccessDenied",
            )
        return category

    async def create_for_user(self, body: CategoryCreate, user_id: str) -> Category:
        return await self.create(Category(**body.model_dump(), user_id=user_id))

    async def update_for_user(
        self, id: str, diff: CategoryUpdate, user_id: str
    ) -> Optional[Category]:
        await self.get_by_id_for_user(id, user_id)  # Check ownership
        return await self.update(id, diff)

    async def delete_for_user(self, id: str, user_id: str):
        await self.get_by_id_for_user(id, user_id)  # Check ownership
        return await self.delete(id)