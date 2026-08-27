from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import DateTime
import uuid


class SaleProduct(SQLModel, table=True):
    __tablename__ = "sale_products"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    sale_id: uuid.UUID = Field(foreign_key="sales.id", nullable=False, index=True)
    product_id: uuid.UUID = Field(foreign_key="products.id", nullable=False, index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    company_id: uuid.UUID = Field(foreign_key="companies.id", nullable=False, index=True)
    quantity: int = Field(nullable=False)
    unit_price: float = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False, sa_type=DateTime(timezone=True))
