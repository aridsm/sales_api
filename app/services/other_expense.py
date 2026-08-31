from sqlalchemy.ext.asyncio import AsyncSession
from app.services.base import BaseService
from app.database.models.other_expense import OtherExpense
from app.services.history import HistoryService
from app.enums.history import ActionType, EntityType
from sqlmodel import select
import uuid
from typing import Any

class OtherExpenseService(BaseService[OtherExpense]):
    def __init__(self, session: AsyncSession):
        super().__init__(OtherExpense, session)
        self.history = HistoryService(session)

    async def create(
        self,
        item: OtherExpense,
        user_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
    ) -> OtherExpense:
        new_item = await super().create(item, user_id=user_id, company_id=company_id)
        self.history.log_action(
            user_id=user_id,
            company_id=company_id,
            action_type=ActionType.CREATE,
            entity_type=EntityType.OTHER_EXPENSE,
            entity_id=new_item.id,
            description=f"Despesa Extra '{new_item.name}' (R$ {f'{new_item.value:.2f}'.replace('.', ',')}) registrada."
        )
        await self.session.commit()
        return new_item

    async def update(
        self,
        id: uuid.UUID,
        diff: Any,
        user_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
    ):
        updated_item = await super().update(
            id, diff, user_id=user_id, company_id=company_id
        )
        self.history.log_action(
            user_id=user_id,
            company_id=company_id,
            action_type=ActionType.UPDATE,
            entity_type=EntityType.OTHER_EXPENSE,
            entity_id=updated_item.id,
            description=f"Despesa Extra '{updated_item.name}' atualizada."
        )
        await self.session.commit()
        return updated_item

    async def delete(
        self,
        id: uuid.UUID,
        company_id: uuid.UUID | str | None = None,
        user_id: uuid.UUID | str | None = None,
    ):
        item_db = await self.get_by_id(id, company_id=company_id)
        self.history.log_action(
            user_id=user_id,
            company_id=company_id,
            action_type=ActionType.DELETE,
            entity_type=EntityType.OTHER_EXPENSE,
            entity_id=id,
            description=f"Despesa Extra '{item_db.name}' excluída."
        )
        await super().delete(id, company_id=company_id, user_id=user_id)

    async def delete_bulk(
        self,
        ids: list[uuid.UUID],
        company_id: uuid.UUID | str | None = None,
        user_id: uuid.UUID | str | None = None,
    ):
        query_names = select(OtherExpense.name).where(OtherExpense.id.in_(ids))
        if company_id:
            query_names = query_names.where(OtherExpense.company_id == company_id)
        result_names = await self.session.execute(query_names)
        deleted_names = ", ".join(result_names.scalars().all())

        self.history.log_action(
            user_id=user_id,
            company_id=company_id,
            action_type=ActionType.DELETE,
            entity_type=EntityType.OTHER_EXPENSE,
            description=f"Múltiplas despesas extras excluídas: {deleted_names}."
        )
        await super().delete_bulk(ids, company_id=company_id, user_id=user_id)
