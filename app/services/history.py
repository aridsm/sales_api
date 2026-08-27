import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.services.base import BaseService
from app.database.models.history import History
from app.enums.history import ActionType, EntityType


class HistoryService(BaseService[History]):
    def __init__(self, session: AsyncSession):
        super().__init__(History, session)

    def log_action(
        self,
        user_id: uuid.UUID | str,
        action_type: ActionType,
        entity_type: EntityType,
        description: str,
        company_id: uuid.UUID | str | None = None,
        entity_id: uuid.UUID | None = None,
        details: dict | None = None,
    ):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(company_id, str):
            company_id = uuid.UUID(company_id)

        history = History(
            user_id=user_id,
            company_id=company_id,
            action_type=action_type.value,
            entity_type=entity_type.value,
            entity_id=entity_id,
            description=description,
            details=details or {},
        )
        self.session.add(history)

    async def get_recent_history(
        self,
        company_id: str,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        start_created_at: datetime | None = None,
        end_created_at: datetime | None = None,
        **kwargs,
    ):
        query = select(History).where(History.company_id == uuid.UUID(company_id))
        if search:
            query = query.where(History.description.ilike(f"%{search}%"))

        if start_created_at:
            query = query.where(History.created_at >= start_created_at)
        if end_created_at:
            query = query.where(History.created_at <= end_created_at)

        query = query.order_by(History.created_at.desc())
        return await super().get_all(
            query=query, company_id=company_id, page=page, page_size=page_size, **kwargs
        )
