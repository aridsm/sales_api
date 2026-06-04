import uuid
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.services.base import BaseService
from app.database.models.sale import Sale
from app.database.models.sale_product import SaleProduct
from app.database.models.product import Product
from app.api.schemas.sale import SaleProductItem
from app.enums.sale import SaleStatus
from sqlalchemy import Select, func
from typing import Any


class SaleService(BaseService[Sale]):
    def __init__(self, session: AsyncSession):
        super().__init__(Sale, session)

    def _get_base_query(self, user_id: str) -> Select:
        return (
            select(Sale, func.count(SaleProduct.id).label("items_count"))
            .outerjoin(SaleProduct, Sale.id == SaleProduct.sale_id)
            .where(Sale.user_id == user_id)
            .group_by(Sale.id)
        )

    async def get_all(
        self, query: Select | None = None, user_id: str | None = None, **kwargs
    ):
        if query is None:
            query = self._get_base_query(user_id=user_id)
        return await super().get_all(query=query, user_id=user_id, **kwargs)

    async def get_by_id(
        self,
        id: uuid.UUID,
        user_id: uuid.UUID | str | None = None,
        query: Select | None = None,
    ) -> Any:
        if query is None:
            query = self._get_base_query(user_id=user_id).where(Sale.id == id)
        return await super().get_by_id(id, user_id=user_id, query=query)

    async def create_sale_with_products(
        self, items: list[SaleProductItem], user_id: uuid.UUID
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
                Product.user_id == user_id,
            )
        )

        products = {p.id: p for p in result.scalars().all()}

        for pid in product_ids:
            if pid not in products:
                raise HTTPException(status_code=404, detail="errorEntityNotFound")

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

        total = sum(
            products[pid].price * qty for pid, qty in product_quantities.items()
        )

        sale = Sale(user_id=user_id, status=SaleStatus.DONE, total=total)
        self.session.add(sale)
        await self.session.flush()

        for pid, qty in product_quantities.items():
            product = products[pid]

            sale_product = SaleProduct(
                sale_id=sale.id,
                product_id=pid,
                user_id=user_id,
                quantity=qty,
                unit_price=product.price,
            )
            self.session.add(sale_product)

            product.stock_amount -= qty
            product.sold_amount += qty

        await self.session.commit()
        await self.session.refresh(sale)

        return await self.get_by_id(sale.id, user_id=user_id)

    async def cancel_sale(self, sale_id: uuid.UUID, user_id: uuid.UUID) -> Sale:
        sale = await self.get_by_id(sale_id, user_id=user_id)

        if sale.status == SaleStatus.CANCELED:
            raise HTTPException(status_code=400, detail="errorSaleAlreadyCanceled")

        result = await self.session.execute(
            select(SaleProduct).where(SaleProduct.sale_id == sale_id)
        )
        sale_products = result.scalars().all()

        product_ids = [sp.product_id for sp in sale_products]

        products_result = await self.session.execute(
            select(Product).where(Product.id.in_(product_ids))
        )
        products = {p.id: p for p in products_result.scalars().all()}

        for sp in sale_products:
            product = products[sp.product_id]
            product.stock_amount += sp.quantity
            product.sold_amount -= sp.quantity

        sale.status = SaleStatus.CANCELED

        await self.session.commit()
        await self.session.refresh(sale)

        return await self.get_by_id(sale.id, user_id=user_id)
