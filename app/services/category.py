from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.base import BaseService
from app.database.models.category import Category
from app.database.models.product import Product
from app.database.models.other_expense import OtherExpense
from app.database.models.sale_product import SaleProduct
from app.database.models.sale import Sale
from app.enums.sale import SaleStatus
import uuid
from fastapi import HTTPException
from typing import Any
from app.services.history import HistoryService
from app.enums.history import ActionType, EntityType


class CategoryService(BaseService[Category]):
    def __init__(self, session: AsyncSession):
        super().__init__(Category, session)
        self.history = HistoryService(session)

    async def create(
        self, item: Category, user_id: uuid.UUID | None = None
    ) -> Category:
        new_item = await super().create(item, user_id)
        self.history.log_action(
            user_id=user_id,
            action_type=ActionType.CREATE,
            entity_type=EntityType.CATEGORY,
            entity_id=new_item.id,
            description=f"Categoria '{new_item.name}' criada.",
        )
        await self.session.commit()
        return new_item

    async def update(self, id: uuid.UUID, diff: Any, user_id: uuid.UUID | None = None):
        updated_item = await super().update(id, diff, user_id)
        self.history.log_action(
            user_id=user_id,
            action_type=ActionType.UPDATE,
            entity_type=EntityType.CATEGORY,
            entity_id=updated_item.id,
            description=f"Categoria '{updated_item.name}' atualizada.",
        )
        await self.session.commit()
        return updated_item

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

        item_db = await self.get_by_id(id, user_id=user_id)
        self.history.log_action(
            user_id=user_id,
            action_type=ActionType.DELETE,
            entity_type=EntityType.CATEGORY,
            entity_id=id,
            description=f"Categoria '{item_db.name}' excluída.",
        )

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
                detail={
                    "error": "errorHasExpenses",
                    "categories": expense_category_names,
                },
            )

        query_names = select(Category.name).where(Category.id.in_(ids))
        if user_id:
            query_names = query_names.where(Category.user_id == user_id)
        result_names = await self.session.execute(query_names)
        deleted_names = ", ".join(result_names.scalars().all())

        self.history.log_action(
            user_id=user_id,
            action_type=ActionType.DELETE,
            entity_type=EntityType.CATEGORY,
            description=f"Múltiplas categorias excluídas: {deleted_names}.",
        )

        await super().delete_bulk(ids, user_id)

    async def get_amounts(
        self,
        user_id: str,
        start_created_at: str | None = None,
        end_created_at: str | None = None,
    ) -> dict:
        query = (
            select(
                Category.id.label("category_id"),
                Category.name.label("category_name"),
                Category.color.label("category_color"),
                func.sum(SaleProduct.unit_price * SaleProduct.quantity).label("value"),
            )
            .join(Product, Product.category_id == Category.id)
            .join(SaleProduct, SaleProduct.product_id == Product.id)
            .join(Sale, Sale.id == SaleProduct.sale_id)
            .where(
                Category.user_id == uuid.UUID(user_id), Sale.status == SaleStatus.DONE
            )
            .group_by(Category.id, Category.name, Category.color)
            .order_by(func.sum(SaleProduct.unit_price * SaleProduct.quantity).desc())
        )

        if start_created_at:
            query = query.where(SaleProduct.created_at >= start_created_at)
        if end_created_at:
            query = query.where(SaleProduct.created_at <= end_created_at)

        result = await self.session.execute(query)
        rows = result.all()

        amounts = []
        total = 0.0
        for row in rows:
            val = float(row.value) if row.value is not None else 0.0
            total += val
            amounts.append(
                {
                    "category_id": str(row.category_id),
                    "category_name": row.category_name,
                    "category_color": row.category_color,
                    "value": val,
                }
            )

        if len(amounts) > 5:
            top_amounts = amounts[:5]
            others_value = sum(item["value"] for item in amounts[5:])
            if others_value > 0:
                top_amounts.append({
                    "category_id": "others",
                    "category_name": "Outros",
                    "category_color": "#808080",
                    "value": others_value
                })
            amounts = top_amounts

        return {
            "items": amounts,
            "total": total
        }
