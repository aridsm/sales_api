from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.api.schemas.user import UserResponse
from app.api.tokens import TokenPayload, decode_jwt_token
from app.database.redis import redis_db
from app.database.engine import get_session
from app.database.models.user import User
from app.database.models.company_user import CompanyUser
from app.enums.company import CompanyPermission
from app.services.user import UserService
from app.services.product import ProductService
from app.services.other_expense import OtherExpenseService
from app.services.history import HistoryService
from app.services.dashboard import DashboardService
from app.services.category import CategoryService
from app.services.sale import SaleService
from app.services.sale_product import SaleProductService
from app.services.stock_entry import StockEntryService
from app.services.stock_entry_product import StockEntryProductService
from app.services.company import CompanyService

security = HTTPBearer()

SessionDependency = Annotated[AsyncSession, Depends(get_session)]

bearer_token = OAuth2PasswordBearer(tokenUrl="/users/login")


async def get_bearer_token(_: SessionDependency, token: str = Depends(bearer_token)):
    token_payload = decode_jwt_token(token)
    if await redis_db.is_token_blacklisted(token_payload.jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "errorInvalidToken"},
        )

    return token_payload


async def get_user_logged(
    session: SessionDependency, token_payload: "TokenDep"
) -> UserResponse:
    res = await session.execute(select(User).where(User.id == token_payload.user_id))

    user = res.scalars().one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "errorUserNotFound"},
        )

    permission = None
    if user.company_id:
        response = await session.execute(
            select(CompanyUser).where(
                CompanyUser.user_id == user.id,
                CompanyUser.company_id == user.company_id,
            )
        )
        company_user = response.scalar_one_or_none()
        if company_user:
            permission = company_user.permission

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        created_at=user.created_at,
        company_id=user.company_id,
        permission=permission,
    )


def require_permission(*allowed: CompanyPermission):
    async def check(
        user: Annotated[UserResponse, Depends(get_user_logged)],
    ) -> UserResponse:
        if user.company_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "errorUserHasNoActiveCompany"},
            )
        if user.permission not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "errorInsufficientPermission"},
            )
        return user

    return check


CanViewDep = Annotated[
    UserResponse,
    Depends(
        require_permission(
            CompanyPermission.VIEW, CompanyPermission.VIEW_EDIT, CompanyPermission.ADMIN
        )
    ),
]
CanEditDep = Annotated[
    UserResponse,
    Depends(require_permission(CompanyPermission.VIEW_EDIT, CompanyPermission.ADMIN)),
]
CanAdminDep = Annotated[
    UserResponse,
    Depends(require_permission(CompanyPermission.ADMIN)),
]


def get_user_service(session: SessionDependency):
    return UserService(session)


def get_product_service(session: SessionDependency):
    return ProductService(session)


def get_other_expense_service(session: SessionDependency):
    return OtherExpenseService(session)


def get_dashboard_service(session: SessionDependency):
    return DashboardService(session)


def get_history_service(session: SessionDependency):
    return HistoryService(session)


def get_category_service(session: SessionDependency):
    return CategoryService(session)


def get_sale_service(session: SessionDependency):
    return SaleService(session)


def get_sale_product_service(session: SessionDependency):
    return SaleProductService(session)


def get_stock_entry_service(session: SessionDependency):
    return StockEntryService(session)


def get_stock_entry_product_service(session: SessionDependency):
    return StockEntryProductService(session)


def get_company_service(session: SessionDependency):
    return CompanyService(session)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
OtherExpenseServiceDep = Annotated[
    OtherExpenseService, Depends(get_other_expense_service)
]
DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]
HistoryServiceDep = Annotated[HistoryService, Depends(get_history_service)]
CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]
SaleServiceDep = Annotated[SaleService, Depends(get_sale_service)]
SaleProductServiceDep = Annotated[SaleProductService, Depends(get_sale_product_service)]
StockEntryServiceDep = Annotated[StockEntryService, Depends(get_stock_entry_service)]
StockEntryProductServiceDep = Annotated[
    StockEntryProductService, Depends(get_stock_entry_product_service)
]
CompanyServiceDep = Annotated[CompanyService, Depends(get_company_service)]
UserLoggedDep = Annotated[UserResponse, Depends(get_user_logged)]
TokenDep = Annotated[TokenPayload, Depends(get_bearer_token)]
