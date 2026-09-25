from uuid import UUID
from fastapi import APIRouter, File, UploadFile, status, Query
from typing import List
from app.api.schemas.company import (
    CompanyCreate,
    CompanyResponse,
    CompanyUpdate,
    CompanyUserAdd,
    CompanyUserUpdate,
    CompanyUserResponse,
    CompanyListItem,
    SwitchCompanyRequest,
    CompanyInvitationResponse,
)
from app.api.dependencies import (
    UserLoggedDep,
    CompanyServiceDep,
)
from app.api.utils.paginated_response import PaginatedResponse
from app.enums.company import InvitationStatus
from app.api.routes.uploads import COMPANY_LOGOS_DIR, save_upload_file, ensure_upload_dirs

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    body: CompanyCreate,
    user: UserLoggedDep,
    service: CompanyServiceDep,
):
    return await service.create_company(body.name, user.id)


@router.get("/", response_model=PaginatedResponse[CompanyListItem])
async def get_my_companies(
    user: UserLoggedDep,
    service: CompanyServiceDep,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
):
    return await service.get_user_companies(
        user.id, page=page, page_size=page_size, search=search
    )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID,
    user: UserLoggedDep,
    service: CompanyServiceDep,
):
    return await service.get_company_by_id(company_id, user.id)


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: UUID,
    body: CompanyUpdate,
    user: UserLoggedDep,
    service: CompanyServiceDep,
):
    return await service.update_company(
        company_id, body.model_dump(exclude_unset=True), user.id
    )


@router.post("/{company_id}/logo", response_model=CompanyResponse)
async def upload_company_logo(
    company_id: UUID,
    user: UserLoggedDep,
    service: CompanyServiceDep,
    file: UploadFile = File(...),
):
    await service._check_admin(company_id, user.id)
    ensure_upload_dirs()
    url = await save_upload_file(file, COMPANY_LOGOS_DIR, "company-logos")
    return await service.update_company(company_id, {"logo_url": url}, user.id)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: UUID,
    user: UserLoggedDep,
    service: CompanyServiceDep,
):
    await service.delete_company(company_id, user.id)


@router.get(
    "/{company_id}/users", response_model=PaginatedResponse[CompanyUserResponse]
)
async def get_company_users(
    company_id: UUID,
    user: UserLoggedDep,
    service: CompanyServiceDep,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
):
    return await service.get_company_users(
        company_id, user.id, page=page, page_size=page_size, search=search
    )


@router.get(
    "/{company_id}/invitations",
    response_model=List[CompanyInvitationResponse],
)
async def get_invitations(
    company_id: UUID,
    user: UserLoggedDep,
    service: CompanyServiceDep,
    status: InvitationStatus | None = None,
):
    return await service.get_company_invitations(company_id, user.id, status=status)


@router.post(
    "/{company_id}/users",
    response_model=CompanyInvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite_user_to_company(
    company_id: UUID,
    body: CompanyUserAdd,
    user: UserLoggedDep,
    service: CompanyServiceDep,
):
    invitation = await service.invite_user(
        company_id, body.email, body.permission, user.id
    )

    from app.api.websocket import ws_manager

    invited_user_id = str(invitation.user_id)
    await ws_manager.send_to_user(
        invited_user_id,
        {
            "type": "company_invitation",
            "invitation_id": str(invitation.id),
            "company_id": str(company_id),
            "invited_by": user.name,
            "permission": body.permission.value,
        },
    )
    return invitation


@router.patch(
    "/{company_id}/users/{target_user_id}", response_model=CompanyUserResponse
)
async def update_company_user(
    company_id: UUID,
    target_user_id: UUID,
    body: CompanyUserUpdate,
    user: UserLoggedDep,
    service: CompanyServiceDep,
):
    cu = await service.update_company_user(
        company_id, target_user_id, body.model_dump(exclude_unset=True), user.id
    )
    return cu


@router.delete("/{company_id}/users/me", status_code=status.HTTP_204_NO_CONTENT)
async def remove_me_from_company(
    company_id: UUID,
    user: UserLoggedDep,
    service: CompanyServiceDep,
):
    await service.remove_me(company_id, user.id)


@router.delete(
    "/{company_id}/users/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_user_from_company(
    company_id: UUID,
    target_user_id: UUID,
    user: UserLoggedDep,
    service: CompanyServiceDep,
):
    await service.remove_user(company_id, target_user_id, user.id)
