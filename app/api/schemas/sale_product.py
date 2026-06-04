from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class SaleProductCreate(BaseModel):
    sale_id: UUID
    product_id: UUID
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)


class SaleProductUpdate(BaseModel):
    quantity: Optional[int] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, gt=0)


class SaleProductResponse(BaseModel):
    id: UUID
    sale_id: UUID
    product_id: UUID
    user_id: UUID
    quantity: int
    unit_price: float
    created_at: datetime
    product_name: Optional[str] = None
    category_id: Optional[UUID] = None
    category_name: Optional[str] = None
    category_color: Optional[str] = None


class SaleProductBulkDelete(BaseModel):
    ids: list[UUID]
