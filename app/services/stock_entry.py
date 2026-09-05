import uuid
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy import Select, func
from typing import Any
from datetime import datetime

from app.services.base import BaseService
from app.database.models.stock_entry import StockEntry
from app.database.models.stock_entry_product import StockEntryProduct
from app.database.models.product import Product
from app.database.models.user import User
from app.api.schemas.stock_entry import StockEntryProductItem
from app.enums.stock_entry import StockEntryStatus
from app.services.history import HistoryService
from app.enums.history import ActionType, EntityType


class StockEntryService(BaseService[StockEntry]):
    def __init__(self, session: AsyncSession):
        super().__init__(StockEntry, session)
        self.history = HistoryService(session)

    def get_base_query(self, company_id: str | uuid.UUID) -> Select:
        return (
            select(
                StockEntry,
                func.count(StockEntryProduct.id).label("items_count"),
                User.name.label("created_by_name"),
                User.email.label("created_by_email"),
            )
            .outerjoin(
                StockEntryProduct, StockEntry.id == StockEntryProduct.stock_entry_id
            )
            .outerjoin(User, StockEntry.created_by == User.id)
            .where(StockEntry.company_id == company_id)
            .group_by(StockEntry.id, User.name, User.email)
        )

    async def get_all(
        self,
        query: Select | None = None,
        company_id: str | uuid.UUID | None = None,
        **kwargs,
    ):
        if query is None:
            query = self.get_base_query(company_id=company_id)
        return await super().get_all(query=query, company_id=company_id, **kwargs)

    async def get_by_id(
        self,
        id: uuid.UUID,
        company_id: uuid.UUID | str | None = None,
        query: Select | None = None,
    ) -> Any:
        if query is None:
            query = self.get_base_query(company_id=company_id).where(
                StockEntry.id == id
            )
        return await super().get_by_id(id, company_id=company_id, query=query)

    async def get_entry_with_details(
        self, entry_id: uuid.UUID, company_id: str | uuid.UUID
    ) -> dict:
        query = self.get_base_query(company_id=company_id).where(
            StockEntry.id == entry_id
        )
        res = await self.session.execute(query)
        row = res.mappings().first()
        if not row:
            raise HTTPException(
                status_code=404, detail={"error": "errorEntityNotFound"}
            )

        entry_obj = row["StockEntry"]
        entry_dict = (
            entry_obj.model_dump()
            if hasattr(entry_obj, "model_dump")
            else entry_obj.dict()
        )
        entry_dict["items_count"] = row.get("items_count", 0)
        entry_dict["created_by_name"] = row.get("created_by_name")
        entry_dict["created_by_email"] = row.get("created_by_email")
        return entry_dict

    async def create_entry_with_products(
        self,
        items: list[StockEntryProductItem],
        date: datetime,
        user_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> StockEntry:
        product_quantities: dict[uuid.UUID, int] = {}
        for item in items:
            product_quantities[item.product_id] = (
                product_quantities.get(item.product_id, 0) + item.quantity
            )

        product_ids = list(product_quantities.keys())
        result = await self.session.execute(
            select(Product).where(
                Product.id.in_(product_ids),
                Product.company_id == company_id,
            )
        )

        products = {p.id: p for p in result.scalars().all()}

        for pid in product_ids:
            if pid not in products:
                raise HTTPException(
                    status_code=404, detail={"error": "errorEntityNotFound"}
                )

        total = sum(item.unit_price * item.quantity for item in items)

        entry = StockEntry(
            user_id=user_id,
            created_by=user_id,
            company_id=company_id,
            status=StockEntryStatus.OPEN,
            total=total,
            date=date,
        )
        self.session.add(entry)
        await self.session.flush()

        for item in items:
            product = products[item.product_id]

            entry_product = StockEntryProduct(
                stock_entry_id=entry.id,
                product_id=item.product_id,
                user_id=user_id,
                company_id=company_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            self.session.add(entry_product)

            product.stock_amount += item.quantity

        self.history.log_action(
            user_id=user_id,
            company_id=company_id,
            action_type=ActionType.CREATE,
            entity_type=EntityType.STOCK_ENTRY,
            entity_id=entry.id,
            description=f"Entrada de Estoque registrada no valor de R$ {f'{total:.2f}'.replace('.', ',')}.",
            details={"total": total, "items_count": sum(product_quantities.values())},
        )

        await self.session.commit()
        await self.session.refresh(entry)

        return await self.get_by_id(entry.id, company_id=company_id)

    async def cancel_entry(
        self, entry_id: uuid.UUID, user_id: uuid.UUID, company_id: uuid.UUID
    ) -> StockEntry:
        entry = await self.get_by_id(entry_id, company_id=company_id)

        if entry.status == StockEntryStatus.CANCELED:
            raise HTTPException(
                status_code=400, detail={"error": "errorStockEntryAlreadyCanceled"}
            )

        result = await self.session.execute(
            select(StockEntryProduct).where(
                StockEntryProduct.stock_entry_id == entry_id
            )
        )
        entry_products = result.scalars().all()

        product_ids = [ep.product_id for ep in entry_products]

        products_result = await self.session.execute(
            select(Product).where(
                Product.id.in_(product_ids), Product.company_id == company_id
            )
        )
        products = {p.id: p for p in products_result.scalars().all()}

        insufficient_products = []
        for ep in entry_products:
            product = products[ep.product_id]
            if product.stock_amount < ep.quantity:
                insufficient_products.append(product.name)

        if insufficient_products:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "errorNoRemainingItems",
                    "products": insufficient_products,
                },
            )

        for ep in entry_products:
            product = products[ep.product_id]
            product.stock_amount -= ep.quantity

        entry.status = StockEntryStatus.CANCELED

        self.history.log_action(
            user_id=user_id,
            company_id=company_id,
            action_type=ActionType.CANCEL,
            entity_type=EntityType.STOCK_ENTRY,
            entity_id=entry.id,
            description=f"Entrada de Estoque (R$ {f'{entry.total:.2f}'.replace('.', ',')}) cancelada.",
        )

        await self.session.commit()
        await self.session.refresh(entry)

        return await self.get_by_id(entry.id, company_id=company_id)
