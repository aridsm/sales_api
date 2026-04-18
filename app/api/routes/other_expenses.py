from uuid import UUID
from fastapi import APIRouter, status

from app.api.schemas.other_expense import (
    OtherExpenseCreate,
    OtherExpenseResponse,
    OtherExpenseUpdate,
)
from app.api.dependencies import UserLoggedDep, OtherExpenseServiceDep

router = APIRouter(prefix="/other_expenses", tags=["other_expenses"])


@router.get("/", response_model=list[OtherExpenseResponse])
async def get_all_other_expenses(
    user: UserLoggedDep,
    service: OtherExpenseServiceDep,
    page: int = 1,
    page_size: int = 20,
):
    result = await service.get_all_for_user(
        user_id=str(user.id), page=page, page_size=page_size
    )
    return result.items


@router.get("/{expense_id}", response_model=OtherExpenseResponse)
async def get_other_expense_by_id(
    expense_id: UUID,
    user: UserLoggedDep,
    service: OtherExpenseServiceDep,
):
    return await service.get_by_id_for_user(str(expense_id), str(user.id))


@router.post(
    "/", response_model=OtherExpenseResponse, status_code=status.HTTP_201_CREATED
)
async def create_other_expense(
    body: OtherExpenseCreate,
    user: UserLoggedDep,
    service: OtherExpenseServiceDep,
):
    return await service.create_for_user(body, str(user.id))


@router.patch("/{expense_id}", response_model=OtherExpenseResponse)
async def update_other_expense(
    expense_id: UUID,
    body: OtherExpenseUpdate,
    user: UserLoggedDep,
    service: OtherExpenseServiceDep,
):
    return await service.update_for_user(str(expense_id), body, str(user.id))


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_other_expense(
    expense_id: UUID,
    user: UserLoggedDep,
    service: OtherExpenseServiceDep,
):
    await service.delete_for_user(str(expense_id), str(user.id))
