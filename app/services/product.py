from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from fastapi import HTTPException
import uuid
from app.services.base import BaseService
from app.database.models.product import Product
from app.database.models.sale_product import SaleProduct
from app.database.models.sale import Sale
from app.enums.sale import SaleStatus
from app.services.history import HistoryService
from app.enums.history import ActionType, EntityType
from typing import Any


class ProductService(BaseService[Product]):
    def __init__(self, session: AsyncSession):
        super().__init__(Product, session)
        self.history = HistoryService(session)

    async def create(self, item: Product, user_id: uuid.UUID | None = None) -> Product:
        new_item = await super().create(item, user_id)
        self.history.log_action(
            user_id=user_id,
            action_type=ActionType.CREATE,
            entity_type=EntityType.PRODUCT,
            entity_id=new_item.id,
            description=f"Produto '{new_item.name}' criado."
        )
        await self.session.commit()
        return new_item

    async def update(self, id: uuid.UUID, diff: Any, user_id: uuid.UUID | None = None):
        updated_item = await super().update(id, diff, user_id)
        self.history.log_action(
            user_id=user_id,
            action_type=ActionType.UPDATE,
            entity_type=EntityType.PRODUCT,
            entity_id=updated_item.id,
            description=f"Produto '{updated_item.name}' atualizado."
        )
        await self.session.commit()
        return updated_item

    async def delete(self, id: uuid.UUID, user_id: uuid.UUID | str | None = None):
        query = (
            select(Product.name)
            .join(SaleProduct, SaleProduct.product_id == Product.id)
            .join(Sale, Sale.id == SaleProduct.sale_id)
            .where(Product.id == id, Sale.status == SaleStatus.DONE)
        )
        if user_id:
            query = query.where(Product.user_id == user_id)

        result = await self.session.execute(query)
        product_name = result.scalar_one_or_none()

        if product_name is not None:
            raise HTTPException(status_code=400, detail={"error": "errorHasDoneSales"})

        item_db = await self.get_by_id(id, user_id=user_id)
        self.history.log_action(
            user_id=user_id,
            action_type=ActionType.DELETE,
            entity_type=EntityType.PRODUCT,
            entity_id=id,
            description=f"Produto '{item_db.name}' excluído."
        )

        await super().delete(id, user_id)

    async def delete_bulk(
        self, ids: list[uuid.UUID], user_id: uuid.UUID | str | None = None
    ):
        query = (
            select(Product.name)
            .join(SaleProduct, SaleProduct.product_id == Product.id)
            .join(Sale, Sale.id == SaleProduct.sale_id)
            .where(Product.id.in_(ids), Sale.status == SaleStatus.DONE)
        )
        if user_id:
            query = query.where(Product.user_id == user_id)

        result = await self.session.execute(query)
        product_names = list(set(result.scalars().all()))

        if product_names:
            raise HTTPException(
                status_code=400,
                detail={"error": "errorHasDoneSales", "products": product_names},
            )

        query_names = select(Product.name).where(Product.id.in_(ids))
        if user_id:
            query_names = query_names.where(Product.user_id == user_id)
        result_names = await self.session.execute(query_names)
        deleted_names = ", ".join(result_names.scalars().all())

        self.history.log_action(
            user_id=user_id,
            action_type=ActionType.DELETE,
            entity_type=EntityType.PRODUCT,
            description=f"Múltiplos produtos excluídos: {deleted_names}."
        )

        await super().delete_bulk(ids, user_id)
