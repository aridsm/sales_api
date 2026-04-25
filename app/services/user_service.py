import uuid
from typing import List, Optional, TypeVar, Generic, Type, Any, Protocol
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.services.base import BaseService

class UserOwnedModel(Protocol):
    id: Any
    user_id: Any


T = TypeVar("T", bound=UserOwnedModel)
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

    async def get_by_id_for_user(
        self, id: str, user_id: str
    ) -> T:
        item = await self.get_by_id(uuid.UUID(str(id)) if isinstance(id, str) else id)
        if str(item.user_id) != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="errorAccessDenied",
            )
        return item

    async def create_for_user(
        self, body: CreateSchema, user_id: str
    ) -> T:
        return await self.create(self.model(**body.model_dump(), user_id=user_id))

    async def update_for_user(
        self, id: str, diff: UpdateSchema, user_id: str
    ) -> Optional[T]:
        await self.get_by_id_for_user(id, user_id)
        return await self.update(uuid.UUID(id), diff)

    async def delete_for_user(self, id: str, user_id: str):
        await self.get_by_id_for_user(id, user_id)
        return await self.delete(uuid.UUID(id))

    async def delete_bulk_for_user(self, ids: List[str], user_id: str):
        processed_ids = [uuid.UUID(id) for id in ids]
        query = (
            delete(self.model)
            .where(self.model.id.in_(processed_ids))
            .where(self.model.user_id == user_id)
        )
        await self.session.execute(query)
        await self.session.commit()
