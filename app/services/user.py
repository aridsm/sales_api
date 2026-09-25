from datetime import datetime, timedelta, timezone
import uuid

import bcrypt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.user import TokenResponse, UserCreate
from app.api.tokens import TokenPayload, create_access_token, decode_jwt_token
from app.database.models.user import User
from app.config import settings
from app.database.redis import redis_db


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def signup(self, body: UserCreate) -> User:
        existing_user = await self.get_by_email(body.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "errorEmailAlreadyRegistered"},
            )

        password_hash = self.hash_password(body.password)
        user = User(**body.model_dump(), password_hash=password_hash)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def login(self, body: OAuth2PasswordRequestForm) -> TokenResponse:
        user = await self.get_by_email(body.username)
        if not user or not self.verify_password(body.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "errorInvalidCredentials"},
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
                detail={"error": "errorInvalidRefreshToken"},
            )

        user = await self.get_by_id(uuid.UUID(token_payload.user_id))

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

    async def get_by_id(self, id: uuid.UUID) -> User | None:
        query = select(User).where(User.id == id)
        user = (await self.session.execute(query)).scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "errorUserNotFound"},
            )

        return user

    async def get_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        return (await self.session.execute(query)).scalar_one_or_none()

    async def update(self, id: uuid.UUID, data: dict) -> User:
        user = await self.get_by_id(id)

        for key, value in data.items():
            if value is not None:
                setattr(user, key, value)

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, id: uuid.UUID):
        user = await self.get_by_id(id)

        await self.session.delete(user)
        await self.session.commit()

    async def change_password(
        self, id: uuid.UUID, current_password: str, new_password: str
    ) -> None:
        user = await self.get_by_id(id)

        if not self.verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "errorInvalidCurrentPassword"},
            )

        user.password_hash = self.hash_password(new_password)
        await self.session.commit()

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
