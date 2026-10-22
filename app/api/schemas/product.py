from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category_id: UUID
    price: float = Field(default=0, ge=0)
    stock_amount: int = Field(default=0, ge=0)
    sold_amount: int = Field(default=0, ge=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category_id: Optional[UUID] = None
    price: Optional[float] = Field(None, ge=0)
    stock_amount: Optional[int] = Field(None, ge=0)
    sold_amount: Optional[int] = Field(None, ge=0)


class ProductResponse(ProductBase):
    id: UUID
    created_at: datetime
    category_name: Optional[str] = None
    category_color: Optional[str] = None
    created_by: Optional[UUID] = None
    created_by_name: Optional[str] = None
    created_by_email: Optional[str] = None


class ProductBulkDelete(BaseModel):
    ids: list[UUID]
