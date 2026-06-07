from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from fastapi import HTTPException
import uuid
from app.services.base import BaseService
from app.database.models.product import Product
from app.database.models.sale_product import SaleProduct
from app.database.models.sale import Sale
from app.enums.sale import SaleStatus


class ProductService(BaseService[Product]):
    def __init__(self, session: AsyncSession):
        super().__init__(Product, session)

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
                detail={"error": "errorHasDoneSales", "name": product_names},
            )

        await super().delete_bulk(ids, user_id)
