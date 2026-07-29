from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.enums.stock_entry import StockEntryStatus


class StockEntryProductItem(BaseModel):
    product_id: UUID
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)


class StockEntryBase(BaseModel):
    date: datetime
    status: StockEntryStatus = StockEntryStatus.OPEN


class StockEntryCreate(StockEntryBase):
    products: list[StockEntryProductItem] = Field(..., min_length=1)


class StockEntryResponse(StockEntryBase):
    id: UUID
    code: int | None = None
    total: float
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    items_count: Optional[int] = None


class StockEntryBulkDelete(BaseModel):
    ids: list[UUID]
