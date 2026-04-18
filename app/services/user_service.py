from typing import Optional, TypeVar, Generic, Type
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.services.base import BaseService

T = TypeVar("T")
CreateSchema = TypeVar("CreateSchema", bound=BaseModel)
UpdateSchema = TypeVar("UpdateSchema", bound=BaseModel)


class UserOwnedService(BaseService[T], Generic[T, CreateSchema, UpdateSchema]):
    def __init__(self, model: Type[T], session: AsyncSession):
        super().__init__(model, session)

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

    async def get_by_id_for_user(self, id: str, user_id: str) -> Optional[T]:
        item = await self.get_by_id(id)
        if str(item.user_id) != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="errorAccessDenied",
            )
        return item

    async def create_for_user(self, body: CreateSchema, user_id: str) -> T:
        return await self.create(self.model(**body.model_dump(), user_id=user_id))

    async def update_for_user(
        self, id: str, diff: UpdateSchema, user_id: str
    ) -> Optional[T]:
        await self.get_by_id_for_user(id, user_id)  # Check ownership
        return await self.update(id, diff)

    async def delete_for_user(self, id: str, user_id: str):
        await self.get_by_id_for_user(id, user_id)  # Check ownership
        return await self.delete(id)
