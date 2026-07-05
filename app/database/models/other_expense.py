from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import DateTime
import uuid


class OtherExpense(SQLModel, table=True):
    """Other expense model"""

    __tablename__ = "other_expenses"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    description: str | None = Field(default=None, max_length=1024)
    value: float = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False, sa_type=DateTime(timezone=True))
    date: datetime = Field(nullable=False, sa_type=DateTime(timezone=True), index=True)
    category_id: uuid.UUID = Field(foreign_key="categories.id", nullable=False, index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)

    # def __repr__(self):
    #     return f"<OtherExpense(id={self.id}, name={self.name}, category_id={self.category_id}, value={self.value})>"
