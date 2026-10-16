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
    discount: float = Field(default=0.0, ge=0)
    products: list[SaleProductItem] = Field(..., min_length=1)


class SaleUpdate(BaseModel):
    status: Optional[SaleStatus] = None


class SaleResponse(BaseModel):
    id: UUID
    code: int
    status: SaleStatus
    total: float
    discount: float = 0.0
    user_id: UUID
    created_by: Optional[UUID] = None
    created_by_name: Optional[str] = None
    created_by_email: Optional[str] = None
    created_by_avatar_url: Optional[str] = None
    items_count: int = 0
    created_at: datetime
    updated_at: datetime
    date: datetime


class SaleBulkDelete(BaseModel):
    ids: list[UUID]
