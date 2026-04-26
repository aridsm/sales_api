from datetime import datetime, timedelta, timezone
import uuid

import bcrypt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.user import TokenResponse, UserCreate, UserLogin
from app.api.tokens import TokenPayload, create_access_token, decode_jwt_token
from app.services.base import BaseService
from app.database.models.user import User
from app.config import settings
from app.database.redis import redis_db


class UserService(BaseService[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def signup(self, body: UserCreate) -> User:
        existing_user = await self.get_by_email(body.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="errorEmailAlreadyRegistered",
            )

        password_hash = self.hash_password(body.password)
        return await self.create(User(**body.__dict__, password_hash=password_hash))

    async def login(self, body: OAuth2PasswordRequestForm) -> TokenResponse:
        user = await self.get_by_email(body.username)
        if not user or not self.verify_password(body.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="errorInvalidCredentials",
            )

        access_token = create_access_token(
            email=user.email,
            user_id=user.id,
            type="access",
        )

        refresh_token = create_access_token(
            email=user.email,
            user_id=user.id,
            type="refresh",
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc)
            + (timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)),
        )

    async def logout(self, token: TokenPayload):
        await redis_db.add_token_to_blacklist(token.jti)

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        token_payload = decode_jwt_token(refresh_token)

        if await redis_db.is_token_blacklisted(token_payload.jti):
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="errorInvalidRefreshToken",
            )

        user = await self.get_by_id(uuid.UUID(token_payload.user_id))

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="errorUserNotFound",
            )

        new_access_token = create_access_token(
            email=user.email,
            user_id=user.id,
            type="access",
        )

        new_refresh_token = create_access_token(
            email=user.email,
            user_id=user.id,
            type="refresh",
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_at=datetime.now(timezone.utc)
            + (timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)),
        )

    async def get_by_email(self, email: str) -> User | None:
        query = select(self.model).where(self.model.email == email)
        return (await self.session.execute(query)).scalar_one_or_none()

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
