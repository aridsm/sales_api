from typing import Annotated
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from app.api.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    TokenResponse,
    RefreshToken,
    ChangePasswordRequest,
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
    SessionDependency,
)
from app.database.models.company_user import CompanyUser
from app.enums.company import CompanyPermission
from sqlmodel import select
from app.database.redis import redis_db
from app.api.routes.uploads import (
    AVATARS_DIR,
    save_upload_file,
    ensure_upload_dirs,
    check_upload_rate_limit,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(request: Request, body: UserCreate, service: UserServiceDep):
    client_ip = request.client.host if request.client else "unknown"
    allowed = await redis_db.check_rate_limit(
        f"rate_limit:signup:{client_ip}", max_requests=10, window_seconds=3600
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "errorRateLimitExceeded",
                "message": "Too many signup attempts. Please try again later.",
            },
        )
    return await service.signup(body)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    body: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: UserServiceDep,
):
    client_ip = request.client.host if request.client else "unknown"
    username = body.username.lower().strip()
    allowed = await redis_db.check_rate_limit(
        f"rate_limit:login:{client_ip}:{username}", max_requests=10, window_seconds=60
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "errorRateLimitExceeded",
                "message": "Too many login attempts. Please wait before trying again.",
            },
        )
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
async def update_me(
    body: UserUpdate,
    user: UserLoggedDep,
    service: UserServiceDep,
    session: SessionDependency,
):
    data = body.model_dump(exclude_unset=True)
    job_title = data.pop("job_title", None)

    updated_user = await service.update(user.id, data)

    final_job_title = user.job_title
    if job_title is not None and user.company_id:
        if user.permission == CompanyPermission.ADMIN:
            cu_res = await session.execute(
                select(CompanyUser).where(
                    CompanyUser.user_id == user.id,
                    CompanyUser.company_id == user.company_id,
                )
            )
            company_user = cu_res.scalar_one_or_none()
            if company_user:
                company_user.job_title = job_title
                await session.commit()
                final_job_title = job_title

    return UserResponse(
        **updated_user.model_dump(),
        permission=user.permission,
        job_title=final_job_title,
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: ChangePasswordRequest,
    user: UserLoggedDep,
    service: UserServiceDep,
):
    allowed = await redis_db.check_rate_limit(
        f"rate_limit:change_pwd:{user.id}", max_requests=5, window_seconds=60
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "errorRateLimitExceeded",
                "message": "Too many password change attempts. Please wait before trying again.",
            },
        )
    await service.change_password(user.id, body.current_password, body.new_password)


@router.post("/me/avatar", response_model=UserResponse)
async def upload_my_avatar(
    user: UserLoggedDep,
    service: UserServiceDep,
    file: UploadFile = File(...),
):
    await check_upload_rate_limit(user.id)
    ensure_upload_dirs()
    url = await save_upload_file(file, AVATARS_DIR, "avatars")
    updated_user = await service.update(user.id, {"avatar_url": url})
    return UserResponse(
        **updated_user.model_dump(),
        permission=user.permission,
        job_title=user.job_title,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(service: UserServiceDep, token: TokenDep):
    await service.logout(token)


@router.post("/switch-company", response_model=UserResponse)
async def switch_company(
    body: SwitchCompanyRequest,
    user: UserLoggedDep,
    company_service: CompanyServiceDep,
    session: SessionDependency,
):
    new_permission = await company_service.switch_company(user.id, body.company_id)
    cu_res = await session.execute(
        select(CompanyUser).where(
            CompanyUser.user_id == user.id,
            CompanyUser.company_id == body.company_id,
        )
    )
    cu = cu_res.scalar_one_or_none()
    new_job_title = cu.job_title if cu else None
    return UserResponse(
        **{
            **user.model_dump(exclude=["permission", "job_title"]),
            "company_id": body.company_id,
        },
        permission=new_permission,
        job_title=new_job_title,
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
