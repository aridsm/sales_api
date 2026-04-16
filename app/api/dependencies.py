from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.api.tokens import TokenPayload, decode_jwt_token
from app.database.redis import redis_db
from app.database.engine import get_session
from app.database.models.user import User
from app.services.user import UserService

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


async def get_user_logged(session: SessionDependency, token_payload: "TokenDep"):
    res = await session.execute(select(User).where(User.id == token_payload.user_id))

    user = res.scalars().one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="errorUserNotFound",
        )

    return user


def get_user_service(session: SessionDependency):
    return UserService(session)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
UserLoggedDep = Annotated[User, Depends(get_user_logged)]
TokenDep = Annotated[TokenPayload, Depends(get_bearer_token)]
