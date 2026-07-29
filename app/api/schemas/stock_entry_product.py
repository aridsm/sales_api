from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class StockEntryProductBase(BaseModel):
    product_id: UUID
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)


class StockEntryProductCreate(StockEntryProductBase):
    stock_entry_id: UUID


class StockEntryProductResponse(StockEntryProductBase):
    id: UUID
    stock_entry_id: UUID
    user_id: UUID
    created_at: datetime
    product_name: str | None = None
    category_name: str | None = None
    category_color: str | None = None


class StockEntryProductBulkDelete(BaseModel):
    ids: list[UUID]
