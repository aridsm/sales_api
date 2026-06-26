from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, status, Query
from sqlmodel import select

from app.api.schemas.other_expense import (
    OtherExpenseBulkDelete,
    OtherExpenseCreate,
    OtherExpenseResponse,
    OtherExpenseUpdate,
)
from app.api.dependencies import UserLoggedDep, OtherExpenseServiceDep
from app.api.utils.paginated_response import PaginatedResponse
from app.database.models.other_expense import OtherExpense
from app.database.models.category import Category

router = APIRouter(prefix="/other_expenses", tags=["other_expenses"])


@router.get("/", response_model=PaginatedResponse[OtherExpenseResponse])
async def get_all_other_expenses(
    user: UserLoggedDep,
    service: OtherExpenseServiceDep,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    start_created_at: datetime | None = Query(None),
    end_created_at: datetime | None = Query(None),
):
    query = (
        select(OtherExpense, Category.name.label("category_name"), Category.color.label("category_color"))
        .outerjoin(Category, OtherExpense.category_id == Category.id)
    )

    if start_created_at:
        query = query.where(OtherExpense.date >= start_created_at)
    if end_created_at:
        query = query.where(OtherExpense.date <= end_created_at)

    result = await service.get_all(
        query=query, user_id=str(user.id), page=page, page_size=page_size, search=search
    )
    return result


@router.get("/{expense_id}", response_model=OtherExpenseResponse)
async def get_other_expense_by_id(
    expense_id: UUID,
    user: UserLoggedDep,
    service: OtherExpenseServiceDep,
):
    return await service.get_by_id(expense_id, str(user.id))


@router.post(
    "/", response_model=OtherExpenseResponse, status_code=status.HTTP_201_CREATED
)
async def create_other_expense(
    body: OtherExpenseCreate,
    user: UserLoggedDep,
    service: OtherExpenseServiceDep,
):
    return await service.create(OtherExpense(**body.model_dump()), user.id)


@router.patch("/{expense_id}", response_model=OtherExpenseResponse)
async def update_other_expense(
    expense_id: UUID,
    body: OtherExpenseUpdate,
    user: UserLoggedDep,
    service: OtherExpenseServiceDep,
):
    return await service.update(expense_id, body, user.id)


@router.delete("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bulk_other_expenses(
    body: OtherExpenseBulkDelete,
    user: UserLoggedDep,
    service: OtherExpenseServiceDep,
):
    await service.delete_bulk(body.ids, str(user.id))


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_other_expense(
    expense_id: UUID,
    user: UserLoggedDep,
    service: OtherExpenseServiceDep,
):
    await service.delete(expense_id, str(user.id))
