from math import ceil
from typing import TypeVar, Generic, Type, Optional
import uuid
from fastapi import HTTPException
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.api.utils.paginated_response import PaginatedResponse

T = TypeVar("T")


class BaseService(Generic[T]):
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_all(
        self,
        query: Select | None = None,
        page_size: int = 20,
        page: int = 1,
        get_all=False,
    ) -> PaginatedResponse[T]:
        if query is None:
            query = select(self.model)

        if get_all:
            items = (await self.session.scalars(query)).all()
        else:
            items = (
                await self.session.scalars(
                    query.limit(page_size).offset((page - 1) * page_size)
                )
            ).all()

        query_count = query.order_by(None).subquery()

        total_items = await self.session.scalar(
            select(func.count()).select_from(query_count)
        )
        return PaginatedResponse(
            items=items,
            total_items=total_items,
            page=page,
            total_pages=ceil(total_items / page_size),
        )

    async def get_by_id(self, id: uuid.UUID) -> Optional[T]:
        query = select(self.model).where(self.model.id == id)
        item = (await self.session.execute(query)).scalar_one_or_none()
        if item is None:
            raise HTTPException(status_code=404, detail="errorEntityNotFound")
        return item

    async def create(self, item: T) -> T:
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def update(self, id: uuid.UUID, diff: dict) -> Optional[T]:
        item_db = await self.get_by_id(id)

        body = diff.model_dump(exclude_unset=True)
        for key, value in body.items():
            setattr(item_db, key, value)

        await self.session.commit()
        await self.session.refresh(item_db)
        return item_db

    async def delete(self, id: uuid.UUID):
        item_db = await self.get_by_id(id)
        await self.session.delete(item_db)
        await self.session.commit()

    async def exists(self, id: uuid.UUID) -> bool:
        query = select(self.model).where(self.model.id == id)
        return (await self.session.execute(query)).scalar_one_or_none() is not None
