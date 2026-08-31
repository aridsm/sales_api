from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional
from app.enums.sale import SaleStatus


class SaleProductItem(BaseModel):
    product_id: UUID
    quantity: int = Field(..., gt=0)


from datetime import timezone

class SaleCreate(BaseModel):
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    products: list[SaleProductItem] = Field(..., min_length=1)


class SaleUpdate(BaseModel):
    status: Optional[SaleStatus] = None


class SaleResponse(BaseModel):
    id: UUID
    code: int
    status: SaleStatus
    total: float
    user_id: UUID
    items_count: int = 0
    created_at: datetime
    updated_at: datetime
    date: datetime


class SaleBulkDelete(BaseModel):
    ids: list[UUID]
