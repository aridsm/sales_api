from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional
from app.enums.stock_entry import StockEntryStatus


class StockEntryProductItem(BaseModel):
    product_id: UUID
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)


class StockEntryBase(BaseModel):
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: StockEntryStatus = StockEntryStatus.OPEN


class StockEntryCreate(StockEntryBase):
    discount: float = Field(default=0.0, ge=0)
    products: list[StockEntryProductItem] = Field(..., min_length=1)


class StockEntryResponse(StockEntryBase):
    id: UUID
    code: int | None = None
    total: float
    discount: float = 0.0
    user_id: UUID
    created_by: Optional[UUID] = None
    created_by_name: Optional[str] = None
    created_by_email: Optional[str] = None
    created_by_avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items_count: Optional[int] = None


class StockEntryBulkDelete(BaseModel):
    ids: list[UUID]
