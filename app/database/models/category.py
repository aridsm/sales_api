from datetime import datetime, timezone
from sqlalchemy import DateTime
from pydantic import ConfigDict
from sqlmodel import SQLModel, Field
import uuid
from app.enums.category import CategoryType


class Category(SQLModel, table=True):
    __tablename__ = "categories"
    __sorts__ = ["created_at", "id", "name", "type"]

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    color: str | None = Field(default=None, max_length=7)
    type: CategoryType = Field(nullable=False)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False, sa_type=DateTime(timezone=True))

    @property
    def products(self) -> int:
        return getattr(self, "_products_value", 0)
    
    @products.setter
    def products(self, value: int):
        object.__setattr__(self, "_products_value", value)
