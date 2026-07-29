from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
import uuid
from sqlalchemy import DateTime, Column, Integer, Identity
from app.enums.stock_entry import StockEntryStatus


class StockEntry(SQLModel, table=True):
    __tablename__ = "stock_entries"
    __sorts__ = ["created_at", "updated_at", "date", "id", "code"]

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)

    code: int | None = Field(
        default=None,
        sa_column=Column(
            Integer, Identity(start=1, increment=1), unique=True, nullable=False
        ),
    )

    status: StockEntryStatus = Field(default=StockEntryStatus.OPEN, nullable=False, index=True)
    total: float = Field(default=0, nullable=False)
    date: datetime = Field(nullable=False, sa_type=DateTime(timezone=True), index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
        sa_type=DateTime(timezone=True),
        nullable=False,
    )
