from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
import uuid
from sqlalchemy import Column, DateTime, Integer, Identity, ForeignKey
from app.enums.sale import SaleStatus


class Sale(SQLModel, table=True):
    __tablename__ = "sales"
    __sorts__ = ["created_at", "updated_at", "code", "id"]

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)

    code: int | None = Field(
        default=None,
        sa_column=Column(
            Integer, Identity(start=1, increment=1), unique=True, nullable=False
        ),
    )

    status: SaleStatus = Field(default=SaleStatus.DONE, nullable=False, index=True)
    total: float = Field(default=0, nullable=False)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    company_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    date: datetime = Field(nullable=False, sa_type=DateTime(timezone=True), index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_type=DateTime(timezone=True),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
        sa_type=DateTime(timezone=True),
        nullable=False,
    )
