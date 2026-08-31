from math import ceil
from typing import TypeVar, Generic, Type, Optional, Any
import uuid
from fastapi import HTTPException
from sqlalchemy import Select, and_, or_, case, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import false as sa_false
from sqlmodel import func, select

from app.api.utils.paginated_response import PaginatedResponse
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:

    class Identifiable(Protocol):
        id: Any

    T = TypeVar("T", bound=Identifiable)
else:
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
        get_all: bool = False,
        search: str | None = None,
        sort: str | None = None,
        company_id: uuid.UUID | str | None = None,
        user_id: uuid.UUID | str | None = None,
        include_ids: list[uuid.UUID] | None = None,
        exclude_ids: list[uuid.UUID] | None = None,
        **filters,
    ) -> PaginatedResponse[Any]:
        if query is None:
            query = select(self.model)

        # Filter by company_id (tenant isolation)
        model_company_id = getattr(self.model, "company_id", None)
        if model_company_id is not None:
            if company_id:
                query = query.where(model_company_id == company_id)
            else:
                # No company selected — return empty results
                query = query.where(sa_false())

        soft_filters = []
        if search and hasattr(self.model, "name"):
            model_name = getattr(self.model, "name")
            soft_filters.append(model_name.ilike(f"%{search}%"))

        for key, value in filters.items():
            if value is not None:
                field = getattr(self.model, key, None)
                if field:
                    if isinstance(value, list) and len(value) > 0:
                        soft_filters.append(field.in_(value))
                    elif not isinstance(value, list):
                        soft_filters.append(field == value)

        if include_ids and len(include_ids) > 0:
            if soft_filters:
                query = query.where(
                    or_(self.model.id.in_(include_ids), and_(*soft_filters))
                )
            else:
                pass

            query = query.order_by(case({self.model.id.in_(include_ids): 0}, else_=1))
        else:
            for f in soft_filters:
                query = query.where(f)

        if exclude_ids and len(exclude_ids) > 0:
            query = query.where(self.model.id.notin_(exclude_ids))

        if sort:
            allowed_sorts = getattr(self.model, "__sorts__", [])
            field_name = sort.lstrip("-")
            if field_name in allowed_sorts:
                descending = sort.startswith("-")
                field = getattr(self.model, field_name, None)
                if field:
                    query = query.order_by(field.desc() if descending else field.asc())

        if get_all:
            res = await self.session.execute(query)
        else:
            res = await self.session.execute(
                query.limit(page_size).offset((page - 1) * page_size)
            )

        rows = res.all()
        keys = list(res.keys())
        items = []

        for row in rows:
            if len(row) > 1:
                obj = row[0]
                obj_dict = (
                    obj.model_dump() if hasattr(obj, "model_dump") else obj.dict()
                )

                for i, key in enumerate(keys[1:], 1):
                    obj_dict[key] = row[i]

                items.append(obj_dict)
            else:
                items.append(row[0])

        query_count = query.order_by(None).subquery()

        total_items = (
            await self.session.scalar(select(func.count()).select_from(query_count))
            or 0
        )

        return PaginatedResponse(
            items=items,
            total_items=total_items,
            page=page,
            total_pages=ceil(total_items / page_size) if page_size > 0 else 1,
        )

    async def get_by_id(
        self,
        id: uuid.UUID,
        company_id: uuid.UUID | str | None = None,
        user_id: uuid.UUID | str | None = None,
        query: Select | None = None,
    ) -> T:
        if query is None:
            query = select(self.model).where(self.model.id == id)
            model_company_id = getattr(self.model, "company_id", None)
            if company_id and model_company_id is not None:
                query = query.where(model_company_id == company_id)

        res = await self.session.execute(query)
        row = res.first()

        if row is None:
            raise HTTPException(status_code=404, detail={"error": "errorEntityNotFound"})

        return row[0]

    async def create(
        self, item: T, user_id: uuid.UUID | None = None, company_id: uuid.UUID | None = None
    ) -> T:
        model_company_id = getattr(self.model, "company_id", None)
        if company_id and model_company_id is not None:
            setattr(item, "company_id", company_id)
        model_user_id = getattr(self.model, "user_id", None)
        if user_id and model_user_id is not None:
            setattr(item, "user_id", user_id)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def update(
        self, id: uuid.UUID, diff: Any, company_id: uuid.UUID | None = None, user_id: uuid.UUID | None = None
    ) -> Optional[T]:
        item_db = await self.get_by_id(id, company_id=company_id)

        if isinstance(diff, dict):
            body = diff
        else:
            body = diff.model_dump(exclude_unset=True)
        for key, value in body.items():
            setattr(item_db, key, value)

        await self.session.commit()
        await self.session.refresh(item_db)
        return item_db

    async def delete(self, id: uuid.UUID, company_id: uuid.UUID | str | None = None, user_id: uuid.UUID | str | None = None):
        item_db = await self.get_by_id(id, company_id=company_id)
        await self.session.delete(item_db)
        await self.session.commit()

    async def delete_bulk(
        self, ids: list[uuid.UUID], company_id: uuid.UUID | str | None = None, user_id: uuid.UUID | str | None = None
    ):
        query = delete(self.model).where(self.model.id.in_(ids))
        model_company_id = getattr(self.model, "company_id", None)
        if company_id and model_company_id is not None:
            query = query.where(model_company_id == company_id)

        await self.session.execute(query)
        await self.session.commit()

    async def exists(
        self, id: uuid.UUID, company_id: uuid.UUID | str | None = None, user_id: uuid.UUID | str | None = None
    ) -> bool:
        query = select(self.model).where(self.model.id == id)
        model_company_id = getattr(self.model, "company_id", None)
        if company_id and model_company_id is not None:
            query = query.where(model_company_id == company_id)
        return (await self.session.execute(query)).scalar_one_or_none() is not None
