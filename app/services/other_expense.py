from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_service import UserOwnedService
from app.database.models.other_expense import OtherExpense
from app.api.schemas.other_expense import OtherExpenseCreate, OtherExpenseUpdate


class OtherExpenseService(
    UserOwnedService[OtherExpense, OtherExpenseCreate, OtherExpenseUpdate]
):
    def __init__(self, session: AsyncSession):
        super().__init__(OtherExpense, session)
