from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from fastapi import HTTPException
import uuid
from app.services.base import BaseService
from app.database.models.product import Product
from app.database.models.sale_product import SaleProduct
from app.database.models.stock_entry_product import StockEntryProduct
from app.database.models.sale import Sale
from app.enums.sale import SaleStatus
from app.services.history import HistoryService
from app.enums.history import ActionType, EntityType
from typing import Any


class ProductService(BaseService[Product]):
    def __init__(self, session: AsyncSession):
        super().__init__(Product, session)
        self.history = HistoryService(session)

    async def create(
        self,
        item: Product,
        user_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
    ) -> Product:
        new_item = await super().create(item, user_id=user_id, company_id=company_id)
        self.history.log_action(
            user_id=user_id,
            company_id=company_id,
            action_type=ActionType.CREATE,
            entity_type=EntityType.PRODUCT,
            entity_id=new_item.id,
            description=f"Produto '{new_item.name}' criado."
        )
        await self.session.commit()
        return new_item

    async def update(
        self,
        id: uuid.UUID,
        diff: Any,
        user_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
    ):
        updated_item = await super().update(
            id, diff, user_id=user_id, company_id=company_id
        )
        self.history.log_action(
            user_id=user_id,
            company_id=company_id,
            action_type=ActionType.UPDATE,
            entity_type=EntityType.PRODUCT,
            entity_id=updated_item.id,
            description=f"Produto '{updated_item.name}' atualizado."
        )
        await self.session.commit()
        return updated_item

    async def delete(
        self,
        id: uuid.UUID,
        company_id: uuid.UUID | str | None = None,
        user_id: uuid.UUID | str | None = None,
    ):
        query_sale = (
            select(Product.name)
            .join(SaleProduct, SaleProduct.product_id == Product.id)
            .where(Product.id == id)
        )
        if company_id:
            query_sale = query_sale.where(Product.company_id == company_id)

        result_sale = await self.session.execute(query_sale)
        product_name = result_sale.scalar_one_or_none()

        if product_name is not None:
            raise HTTPException(
                status_code=400,
                detail={"error": "errorHasDoneSales", "name": product_name, "products": [product_name]},
            )

        query_stock = (
            select(Product.name)
            .join(StockEntryProduct, StockEntryProduct.product_id == Product.id)
            .where(Product.id == id)
        )
        if company_id:
            query_stock = query_stock.where(Product.company_id == company_id)

        result_stock = await self.session.execute(query_stock)
        product_name_stock = result_stock.scalar_one_or_none()

        if product_name_stock is not None:
            raise HTTPException(
                status_code=400,
                detail={"error": "errorHasStockEntries", "name": product_name_stock, "products": [product_name_stock]},
            )

        item_db = await self.get_by_id(id, company_id=company_id)
        self.history.log_action(
            user_id=user_id,
            company_id=company_id,
            action_type=ActionType.DELETE,
            entity_type=EntityType.PRODUCT,
            entity_id=id,
            description=f"Produto '{item_db.name}' excluído."
        )

        await super().delete(id, company_id=company_id, user_id=user_id)

    async def delete_bulk(
        self,
        ids: list[uuid.UUID],
        company_id: uuid.UUID | str | None = None,
        user_id: uuid.UUID | str | None = None,
    ):
        query_sale = (
            select(Product.name)
            .join(SaleProduct, SaleProduct.product_id == Product.id)
            .where(Product.id.in_(ids))
        )
        if company_id:
            query_sale = query_sale.where(Product.company_id == company_id)

        result_sale = await self.session.execute(query_sale)
        product_names = list(set(result_sale.scalars().all()))

        if product_names:
            raise HTTPException(
                status_code=400,
                detail={"error": "errorHasDoneSales", "products": product_names},
            )

        query_stock = (
            select(Product.name)
            .join(StockEntryProduct, StockEntryProduct.product_id == Product.id)
            .where(Product.id.in_(ids))
        )
        if company_id:
            query_stock = query_stock.where(Product.company_id == company_id)

        result_stock = await self.session.execute(query_stock)
        product_names_stock = list(set(result_stock.scalars().all()))

        if product_names_stock:
            raise HTTPException(
                status_code=400,
                detail={"error": "errorHasStockEntries", "products": product_names_stock},
            )

        query_names = select(Product.name).where(Product.id.in_(ids))
        if company_id:
            query_names = query_names.where(Product.company_id == company_id)
        result_names = await self.session.execute(query_names)
        deleted_names = ", ".join(result_names.scalars().all())

        self.history.log_action(
            user_id=user_id,
            company_id=company_id,
            action_type=ActionType.DELETE,
            entity_type=EntityType.PRODUCT,
            description=f"Múltiplos produtos excluídos: {deleted_names}."
        )

        await super().delete_bulk(ids, company_id=company_id, user_id=user_id)
