from datetime import datetime, timedelta, timezone
from typing import Literal
import uuid
from fastapi import HTTPException, status
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from pydantic import BaseModel, EmailStr
from app.config import settings


class TokenPayload(BaseModel):
    jti: str
    email: str
    user_id: str
    type: str
    exp: datetime
    iat: datetime


def create_access_token(
    user_id: uuid.UUID,
    email: EmailStr,
    type: Literal["access", "refresh"] = "access",
) -> str:

    expires_at = (
        type == "access"
        and timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    encoded_jwt = jwt.encode(
        algorithm=settings.JWT_ALGORITHM,
        key=settings.JWT_SECRET,
        claims={
            **TokenPayload(
                jti=str(uuid.uuid4()),
                email=email,
                user_id=str(user_id),
                type=type,
                iat=datetime.now(timezone.utc),
                exp=datetime.now(timezone.utc) + expires_at,
            ).__dict__
        },
    )

    return encoded_jwt


def decode_jwt_token(jwt_token: str) -> TokenPayload:
    try:
        token_dict = jwt.decode(
            token=jwt_token,
            algorithms=[settings.JWT_ALGORITHM],
            key=settings.JWT_SECRET,
        )
        return TokenPayload(**token_dict)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "errorExpiredToken"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "errorInvalidToken"},
        )
