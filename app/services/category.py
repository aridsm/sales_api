from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.base import BaseService
from app.database.models.category import Category
from app.database.models.product import Product
from app.database.models.other_expense import OtherExpense
import uuid
from fastapi import HTTPException


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

    async def delete(self, id: uuid.UUID, user_id: uuid.UUID | str | None = None):
        query = (
            select(Category.name)
            .join(Product, Product.category_id == Category.id)
            .where(Category.id == id)
        )
        if user_id:
            query = query.where(Category.user_id == user_id)

        result = await self.session.execute(query)
        category_name = result.scalar_one_or_none()

        if category_name is not None:
            raise HTTPException(status_code=400, detail={"error": "errorHasProducts"})

        expense_query = (
            select(Category.name)
            .join(OtherExpense, OtherExpense.category_id == Category.id)
            .where(Category.id == id)
        )
        if user_id:
            expense_query = expense_query.where(Category.user_id == user_id)

        expense_result = await self.session.execute(expense_query)
        expense_category_name = expense_result.scalar_one_or_none()

        if expense_category_name is not None:
            raise HTTPException(status_code=400, detail={"error": "errorHasExpenses"})

        await super().delete(id, user_id)

    async def delete_bulk(
        self, ids: list[uuid.UUID], user_id: uuid.UUID | str | None = None
    ):
        query = (
            select(Category.name)
            .join(Product, Product.category_id == Category.id)
            .where(Category.id.in_(ids))
        )
        if user_id:
            query = query.where(Category.user_id == user_id)

        result = await self.session.execute(query)
        category_names = list(set(result.scalars().all()))

        if category_names:
            raise HTTPException(
                status_code=400,
                detail={"error": "errorHasProducts", "categories": category_names},
            )

        expense_query = (
            select(Category.name)
            .join(OtherExpense, OtherExpense.category_id == Category.id)
            .where(Category.id.in_(ids))
        )
        if user_id:
            expense_query = expense_query.where(Category.user_id == user_id)

        expense_result = await self.session.execute(expense_query)
        expense_category_names = list(set(expense_result.scalars().all()))

        if expense_category_names:
            raise HTTPException(
                status_code=400,
                detail={"error": "errorHasExpenses", "name": expense_category_names},
            )

        await super().delete_bulk(ids, user_id)
