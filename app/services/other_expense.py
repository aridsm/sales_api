from sqlalchemy.ext.asyncio import AsyncSession
from app.services.base import BaseService
from app.database.models.other_expense import OtherExpense


class OtherExpenseService(BaseService[OtherExpense]):
    def __init__(self, session: AsyncSession):
        super().__init__(OtherExpense, session)
