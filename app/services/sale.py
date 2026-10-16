import uuid
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.services.base import BaseService
from app.database.models.sale import Sale
from app.database.models.sale_product import SaleProduct
from app.database.models.product import Product
from app.database.models.user import User
from app.api.schemas.sale import SaleProductItem
from app.enums.sale import SaleStatus
from sqlalchemy import Select, func, delete
from typing import Any
from datetime import datetime
from app.services.history import HistoryService
from app.enums.history import ActionType, EntityType


class SaleService(BaseService[Sale]):
    def __init__(self, session: AsyncSession):
        super().__init__(Sale, session)
        self.history = HistoryService(session)

    def get_base_query(self, company_id: str | uuid.UUID) -> Select:
        return (
            select(
                Sale,
                func.count(SaleProduct.id).label("items_count"),
                User.name.label("created_by_name"),
                User.email.label("created_by_email"),
                User.avatar_url.label("created_by_avatar_url"),
            )
            .outerjoin(SaleProduct, Sale.id == SaleProduct.sale_id)
            .outerjoin(User, Sale.created_by == User.id)
            .where(Sale.company_id == company_id)
            .group_by(Sale.id, User.name, User.email, User.avatar_url)
        )

    async def get_all(
        self, query: Select | None = None, company_id: str | uuid.UUID | None = None, **kwargs
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
            query = self.get_base_query(company_id=company_id).where(Sale.id == id)
        return await super().get_by_id(id, company_id=company_id, query=query)

    async def get_sale_with_details(self, sale_id: uuid.UUID, company_id: str | uuid.UUID) -> dict:
        query = self.get_base_query(company_id=company_id).where(Sale.id == sale_id)
        res = await self.session.execute(query)
        row = res.mappings().first()
        if not row:
            raise HTTPException(
                status_code=404, detail={"error": "errorEntityNotFound"}
            )

        sale_obj = row["Sale"]
        sale_dict = (
            sale_obj.model_dump()
            if hasattr(sale_obj, "model_dump")
            else sale_obj.dict()
        )
        sale_dict["items_count"] = row.get("items_count", 0)
        sale_dict["created_by_name"] = row.get("created_by_name")
        sale_dict["created_by_email"] = row.get("created_by_email")
        sale_dict["created_by_avatar_url"] = row.get("created_by_avatar_url")
        return sale_dict

    async def create_sale_with_products(
        self,
        items: list[SaleProductItem],
        date: datetime,
        user_id: uuid.UUID,
        company_id: uuid.UUID,
        discount: float = 0.0,
    ) -> Sale:
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

        for pid, qty in product_quantities.items():
            product = products[pid]
            if product.stock_amount < qty:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "errorInsufficientStock",
                        "product_name": product.name,
                    },
                )

        subtotal = sum(
            products[pid].price * qty for pid, qty in product_quantities.items()
        )
        total = max(0.0, subtotal - discount)

        sale = Sale(
            user_id=user_id,
            created_by=user_id,
            company_id=company_id,
            status=SaleStatus.DONE,
            total=total,
            discount=discount,
            date=date,
        )
        self.session.add(sale)
        await self.session.flush()

        for pid, qty in product_quantities.items():
            product = products[pid]

            sale_product = SaleProduct(
                sale_id=sale.id,
                product_id=pid,
                user_id=user_id,
                company_id=company_id,
                quantity=qty,
                unit_price=product.price,
            )
            self.session.add(sale_product)

            product.stock_amount -= qty
            product.sold_amount += qty

        self.history.log_action(
            user_id=user_id,
            company_id=company_id,
            action_type=ActionType.CREATE,
            entity_type=EntityType.SALE,
            entity_id=sale.id,
            description=f"Venda #{sale.code} registrada no valor de R$ {f'{total:.2f}'.replace('.', ',')}.",
            details={"total": total, "discount": discount, "items_count": len(product_ids)},
        )

        await self.session.commit()
        await self.session.refresh(sale)

        return await self.get_by_id(sale.id, company_id=company_id)

    async def cancel_sale(
        self, sale_id: uuid.UUID, user_id: uuid.UUID, company_id: uuid.UUID
    ) -> Sale:
        sale = await self.get_by_id(sale_id, company_id=company_id)

        if sale.status == SaleStatus.CANCELED:
            raise HTTPException(
                status_code=400, detail={"error": "errorSaleAlreadyCanceled"}
            )

        result = await self.session.execute(
            select(SaleProduct).where(SaleProduct.sale_id == sale_id)
        )
        sale_products = result.scalars().all()

        product_ids = [sp.product_id for sp in sale_products]

        products_result = await self.session.execute(
            select(Product).where(
                Product.id.in_(product_ids), Product.company_id == company_id
            )
        )
        products = {p.id: p for p in products_result.scalars().all()}

        for sp in sale_products:
            product = products[sp.product_id]
            product.stock_amount += sp.quantity
            product.sold_amount -= sp.quantity

        sale.status = SaleStatus.CANCELED

        self.history.log_action(
            user_id=user_id,
            company_id=company_id,
            action_type=ActionType.CANCEL,
            entity_type=EntityType.SALE,
            entity_id=sale.id,
            description=f"Venda #{sale.code} (R$ {f'{sale.total:.2f}'.replace('.', ',')}) cancelada.",
        )

        await self.session.commit()
        await self.session.refresh(sale)

        return await self.get_by_id(sale.id, company_id=company_id)

    async def delete(
        self,
        id: uuid.UUID,
        company_id: uuid.UUID | str | None = None,
        user_id: uuid.UUID | str | None = None,
    ):
        sale = await self.get_by_id(id, company_id=company_id)
        if sale.status != SaleStatus.CANCELED:
            raise HTTPException(
                status_code=400,
                detail={"error": "errorSaleMustBeCanceledBeforeDeletion"},
            )

        self.history.log_action(
            user_id=user_id,
            company_id=company_id,
            action_type=ActionType.DELETE,
            entity_type=EntityType.SALE,
            entity_id=id,
            description=f"Venda #{sale.code} excluída.",
        )

        await self.session.execute(
            delete(SaleProduct).where(SaleProduct.sale_id == id)
        )
        await super().delete(id, company_id=company_id, user_id=user_id)

    async def delete_bulk(
        self,
        ids: list[uuid.UUID],
        company_id: uuid.UUID | str | None = None,
        user_id: uuid.UUID | str | None = None,
    ):
        query = select(Sale).where(Sale.id.in_(ids))
        if company_id:
            query = query.where(Sale.company_id == company_id)
        res = await self.session.execute(query)
        sales = res.scalars().all()
        for s in sales:
            if s.status != SaleStatus.CANCELED:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "errorSaleMustBeCanceledBeforeDeletion"},
                )

        self.history.log_action(
            user_id=user_id,
            company_id=company_id,
            action_type=ActionType.DELETE,
            entity_type=EntityType.SALE,
            entity_id=ids[0] if len(ids) == 1 else uuid.uuid4(),
            description=f"{len(ids)} vendas excluídas.",
        )

        await self.session.execute(
            delete(SaleProduct).where(SaleProduct.sale_id.in_(ids))
        )
        await super().delete_bulk(ids, company_id=company_id, user_id=user_id)
