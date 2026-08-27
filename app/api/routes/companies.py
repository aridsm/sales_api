from uuid import UUID
from fastapi import APIRouter, status, Query

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


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: UUID,
    body: CompanyUpdate,
    user: UserLoggedDep,
    service: CompanyServiceDep,
):
    return await service.update_company(company_id, body.name, user.id)


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


@router.post("/{company_id}/users", status_code=status.HTTP_201_CREATED)
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


@router.patch(
    "/{company_id}/users/{target_user_id}", response_model=CompanyUserResponse
)
async def update_user_permission(
    company_id: UUID,
    target_user_id: UUID,
    body: CompanyUserUpdate,
    user: UserLoggedDep,
    service: CompanyServiceDep,
):
    cu = await service.update_user_permission(
        company_id, target_user_id, body.permission, user.id
    )
    return cu


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
