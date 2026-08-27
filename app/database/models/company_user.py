from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import DateTime, UniqueConstraint
import uuid
from app.enums.company import CompanyPermission


class CompanyUser(SQLModel, table=True):
    __tablename__ = "company_users"
    __table_args__ = (
        UniqueConstraint("company_id", "user_id", name="uq_company_user"),
    )

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    company_id: uuid.UUID = Field(foreign_key="companies.id", nullable=False, index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    permission: CompanyPermission = Field(default=CompanyPermission.VIEW, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_type=DateTime(timezone=True),
    )
