import uuid
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
        entity_id: uuid.UUID | None = None,
        details: dict | None = None,
    ):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        history = History(
            user_id=user_id,
            action_type=action_type.value,
            entity_type=entity_type.value,
            entity_id=entity_id,
            description=description,
            details=details or {},
        )
        self.session.add(history)

    async def get_recent_history(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        **kwargs,
    ):
        query = select(History).where(History.user_id == uuid.UUID(user_id))
        if search:
            query = query.where(History.description.ilike(f"%{search}%"))
        query = query.order_by(History.created_at.desc())
        return await super().get_all(
            query=query, user_id=user_id, page=page, page_size=page_size, **kwargs
        )
