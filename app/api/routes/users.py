from typing import Annotated
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.api.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    TokenResponse,
    RefreshToken,
)
from app.api.schemas.company import (
    SwitchCompanyRequest,
    CompanyInvitationResponse,
)
from app.api.dependencies import (
    TokenDep,
    UserLoggedDep,
    UserServiceDep,
    CompanyServiceDep,
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


@router.patch("/me", response_model=UserResponse)
async def update_me(body: UserUpdate, user: UserLoggedDep, service: UserServiceDep):
    updated_user = await service.update(user.id, body.model_dump(exclude_unset=True))
    return UserResponse(**updated_user.model_dump(), permission=user.permission)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(service: UserServiceDep, token: TokenDep):
    await service.logout(token)


@router.post("/switch-company", response_model=UserResponse)
async def switch_company(
    body: SwitchCompanyRequest,
    user: UserLoggedDep,
    company_service: CompanyServiceDep,
):
    new_permission = await company_service.switch_company(user.id, body.company_id)
    return UserResponse(
        **{**user.model_dump(exclude=["permission"]), "company_id": body.company_id},
        permission=new_permission,
    )


@router.get("/invitations", response_model=list[CompanyInvitationResponse])
async def get_my_invitations(
    user: UserLoggedDep,
    company_service: CompanyServiceDep,
):
    return await company_service.get_user_invitations(user.id)


@router.post(
    "/invitations/{invitation_id}/accept", status_code=status.HTTP_204_NO_CONTENT
)
async def accept_invitation(
    invitation_id: str,
    user: UserLoggedDep,
    company_service: CompanyServiceDep,
):
    from uuid import UUID

    await company_service.accept_invitation(UUID(invitation_id), user.id)


@router.post(
    "/invitations/{invitation_id}/reject", status_code=status.HTTP_204_NO_CONTENT
)
async def reject_invitation(
    invitation_id: str,
    user: UserLoggedDep,
    company_service: CompanyServiceDep,
):
    from uuid import UUID

    await company_service.reject_invitation(UUID(invitation_id), user.id)
