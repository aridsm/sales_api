from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.services.base import BaseService
from app.database.models.other_expense import OtherExpense
from app.api.schemas.other_expense import OtherExpenseCreate, OtherExpenseUpdate


class OtherExpenseService(BaseService[OtherExpense]):
    def __init__(self, session: AsyncSession):
        super().__init__(OtherExpense, session)

    async def get_all_for_user(
        self,
        user_id: str,
        page_size: int = 20,
        page: int = 1,
        get_all=False,
    ):
        query = select(self.model).where(self.model.user_id == user_id)
        return await self.get_all(
            query=query, page_size=page_size, page=page, get_all=get_all
        )

    async def get_by_id_for_user(self, id: str, user_id: str) -> Optional[OtherExpense]:
        expense = await self.get_by_id(id)
        if expense.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="errorAccessDenied",
            )
        return expense

    async def create_for_user(self, body: OtherExpenseCreate, user_id: str) -> OtherExpense:
        return await self.create(OtherExpense(**body.model_dump(), user_id=user_id))

    async def update_for_user(
        self, id: str, diff: OtherExpenseUpdate, user_id: str
    ) -> Optional[OtherExpense]:
        await self.get_by_id_for_user(id, user_id)
        return await self.update(id, diff)

    async def delete_for_user(self, id: str, user_id: str):
        await self.get_by_id_for_user(id, user_id)
        return await self.delete(id)
