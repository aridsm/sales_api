from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.api.schemas.user import (
    UserCreate,
    UserResponse,
    TokenResponse,
    RefreshToken,
)
from app.api.dependencies import (
    TokenDep,
    UserLoggedDep,
    UserServiceDep,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(body: UserCreate, service: UserServiceDep):
    return await service.signup(body)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: Annotated[OAuth2PasswordRequestForm, Depends()], service: UserServiceDep
):
    return await service.login(body)


@router.get("/me", response_model=UserResponse)
async def get_me(user: UserLoggedDep):
    return user


@router.post("/refresh_token", response_model=TokenResponse)
async def refresh_token(
    body: RefreshToken,
    service: UserServiceDep,
):
    return await service.refresh_token(body.refresh_token)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(user: UserLoggedDep, service: UserServiceDep):
    await service.delete(user.id)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(service: UserServiceDep, token: TokenDep):
    await service.logout(token)
