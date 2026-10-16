import hashlib
import json
import secrets
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

    @staticmethod
    def hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    async def signup(self, body: UserCreate) -> tuple[User, str]:
        existing_user = await self.get_by_email(body.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "errorEmailAlreadyRegistered"},
            )

        raw_token = secrets.token_urlsafe(32)
        token_hash = self.hash_token(raw_token)
        verification_expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS
        )

        password_hash = self.hash_password(body.password)
        user = User(
            **body.model_dump(),
            password_hash=password_hash,
            is_verified=False,
            verification_token=token_hash,
            verification_token_expires_at=verification_expires_at,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user, raw_token

    async def verify_email(self, token: str) -> TokenResponse:
        token_hash = self.hash_token(token)
        query = select(User).where(User.verification_token == token_hash)
        user = (await self.session.execute(query)).scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "errorInvalidOrExpiredVerificationToken"},
            )

        if user.verification_token_expires_at and user.verification_token_expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "errorVerificationTokenExpired"},
            )

        user.is_verified = True
        user.verification_token = None
        user.verification_token_expires_at = None
        await self.session.commit()
        await self.session.refresh(user)

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

    async def resend_verification(self, email: str) -> tuple[User | None, str | None]:
        user = await self.get_by_email(email)
        if not user or user.is_verified:
            return None, None

        raw_token = secrets.token_urlsafe(32)
        token_hash = self.hash_token(raw_token)
        user.verification_token = token_hash
        user.verification_token_expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS
        )
        await self.session.commit()
        await self.session.refresh(user)
        return user, raw_token

    async def login(self, body: OAuth2PasswordRequestForm) -> TokenResponse:
        user = await self.get_by_email(body.username)
        if not user or not self.verify_password(body.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "errorInvalidCredentials"},
            )

        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "errorEmailNotVerified"},
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

    async def request_email_change(
        self, user_id: uuid.UUID, new_email: str, password: str
    ) -> tuple[str, str]:
        user = await self.get_by_id(user_id)
        if not self.verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "errorInvalidCurrentPassword"},
            )

        new_email_clean = new_email.lower().strip()
        if new_email_clean == user.email.lower().strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "errorEmailSameAsCurrent"},
            )

        existing_user = await self.get_by_email(new_email_clean)
        if existing_user and existing_user.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "errorEmailAlreadyRegistered"},
            )

        raw_token = secrets.token_urlsafe(32)
        token_hash = self.hash_token(raw_token)
        expire_seconds = settings.EMAIL_VERIFICATION_EXPIRE_HOURS * 3600

        payload = json.dumps(
            {"user_id": str(user.id), "new_email": new_email_clean}
        )
        await redis_db.set_value(
            f"email_change:{token_hash}", payload, expire_seconds
        )

        return new_email_clean, raw_token

    async def confirm_email_change(self, token: str) -> TokenResponse:
        token_hash = self.hash_token(token)
        key = f"email_change:{token_hash}"
        data_str = await redis_db.get_value(key)

        if not data_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "errorInvalidOrExpiredVerificationToken"},
            )

        data = json.loads(data_str)
        user_id = uuid.UUID(data["user_id"])
        new_email = data["new_email"]

        existing_user = await self.get_by_email(new_email)
        if existing_user and existing_user.id != user_id:
            await redis_db.delete_key(key)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "errorEmailAlreadyRegistered"},
            )

        user = await self.get_by_id(user_id)
        user.email = new_email
        user.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(user)

        await redis_db.delete_key(key)

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

    async def request_password_reset(
        self, email: str
    ) -> tuple[User | None, str | None]:
        user = await self.get_by_email(email.lower().strip())
        if not user:
            return None, None

        raw_token = secrets.token_urlsafe(32)
        token_hash = self.hash_token(raw_token)
        expire_seconds = 3600  # 1 hour

        payload = json.dumps({"user_id": str(user.id)})
        await redis_db.set_value(f"pwd_reset:{token_hash}", payload, expire_seconds)

        return user, raw_token

    async def reset_password(self, token: str, new_password: str) -> None:
        token_hash = self.hash_token(token)
        key = f"pwd_reset:{token_hash}"
        data_str = await redis_db.get_value(key)

        if not data_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "errorInvalidOrExpiredResetToken"},
            )

        data = json.loads(data_str)
        user_id = uuid.UUID(data["user_id"])
        user = await self.get_by_id(user_id)

        if not user:
            await redis_db.delete_key(key)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "errorUserNotFound"},
            )

        user.password_hash = self.hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(user)

        await redis_db.delete_key(key)

