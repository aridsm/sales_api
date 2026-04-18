from datetime import datetime
from sqlmodel import SQLModel, Field
import uuid
from app.enums.category import CategoryType


class Category(SQLModel, table=True):
    """Category model"""

    __tablename__ = "categories"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    color: str | None = Field(default=None, max_length=7)
    type: CategoryType = Field(nullable=False)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # def __repr__(self):
    #     return f"<Category(id={self.id}, name={self.name}, type={self.type})>"
