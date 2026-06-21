from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import DateTime
import uuid


class Product(SQLModel, table=True):
    """Product model"""

    __tablename__ = "products"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    category_id: uuid.UUID = Field(foreign_key="categories.id", nullable=False)
    price: float = Field(nullable=False)
    stock_amount: int = Field(default=0, nullable=False)
    sold_amount: int = Field(default=0, nullable=False)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False, sa_type=DateTime(timezone=True))

    # def __repr__(self):
    #     return f"<Product(id={self.id}, name={self.name}, category_id={self.category_id}, price={self.price})>"
