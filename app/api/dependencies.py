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
from app.services.user import UserService
from app.services.product import ProductService
from app.services.other_expense import OtherExpenseService
from app.services.category import CategoryService

security = HTTPBearer()

SessionDependency = Annotated[AsyncSession, Depends(get_session)]

bearer_token = OAuth2PasswordBearer(tokenUrl="/users/login")


async def get_bearer_token(
    session: SessionDependency, token: str = Depends(bearer_token)
):
    token_payload = decode_jwt_token(token)
    if await redis_db.is_token_blacklisted(token_payload.jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="errorInvalidToken",
        )

    res = await session.execute(select(User).where(User.id == token_payload.user_id))
    user = res.scalars().one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="errorUserNotFound",
        )

    return token_payload


async def get_user_logged(session: SessionDependency, token_payload: "TokenDep") -> UserResponse:
    res = await session.execute(select(User).where(User.id == token_payload.user_id))

    user = res.scalars().one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="errorUserNotFound",
        )

    return UserResponse(**user.model_dump())


def get_user_service(session: SessionDependency):
    return UserService(session)


def get_product_service(session: SessionDependency):
    return ProductService(session)


def get_other_expense_service(session: SessionDependency):
    return OtherExpenseService(session)


def get_category_service(session: SessionDependency):
    return CategoryService(session)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
OtherExpenseServiceDep = Annotated[
    OtherExpenseService, Depends(get_other_expense_service)
]
CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]
UserLoggedDep = Annotated[UserResponse, Depends(get_user_logged)]
TokenDep = Annotated[TokenPayload, Depends(get_bearer_token)]
