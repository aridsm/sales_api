import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy import func

from app.database.models.company import Company
from app.database.models.company_user import CompanyUser
from app.database.models.company_invitation import CompanyInvitation
from app.database.models.user import User
from app.enums.company import CompanyPermission, InvitationStatus
from app.api.utils.paginated_response import PaginatedResponse
from sqlalchemy.orm import aliased


class CompanyService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_company(self, name: str, user_id: uuid.UUID) -> Company:
        company = Company(name=name)
        self.session.add(company)
        await self.session.flush()

        company_user = CompanyUser(
            company_id=company.id,
            user_id=user_id,
            permission=CompanyPermission.ADMIN,
        )
        self.session.add(company_user)

        user_res = await self.session.execute(select(User).where(User.id == user_id))
        user = user_res.scalar_one_or_none()
        if user:
            user.company_id = company.id

        await self.session.commit()
        await self.session.refresh(company)
        return company

    async def get_user_companies(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> dict:
        query = (
            select(
                Company,
                CompanyUser.permission,
                CompanyUser.created_at,
            )
            .join(CompanyUser, CompanyUser.company_id == Company.id)
            .where(CompanyUser.user_id == user_id)
        )

        if search:
            query = query.where(Company.name.ilike(f"%{search}%"))

        from sqlalchemy import func as sa_func

        count_query = query.order_by(None).subquery()
        total_items = (
            await self.session.scalar(select(sa_func.count()).select_from(count_query))
            or 0
        )

        query = query.order_by(Company.name.asc())
        query = query.limit(page_size).offset((page - 1) * page_size)

        result = await self.session.execute(query)
        rows = result.all()

        from math import ceil

        items = [
            {
                "id": row[0].id,
                "name": row[0].name,
                "logo_url": row[0].logo_url,
                "document": row[0].document,
                "email": row[0].email,
                "phone": row[0].phone,
                "website": row[0].website,
                "zip_code": row[0].zip_code,
                "street": row[0].street,
                "number": row[0].number,
                "complement": row[0].complement,
                "neighborhood": row[0].neighborhood,
                "city": row[0].city,
                "state": row[0].state,
                "permission": row[1],
                "created_at": row[0].created_at,
                "updated_at": row[0].updated_at,
            }
            for row in rows
        ]

        return PaginatedResponse(
            items=items,
            total_items=total_items,
            page=page,
            total_pages=ceil(total_items / page_size) if page_size > 0 else 1,
        )

    async def get_company_by_id(
        self, company_id: uuid.UUID, user_id: uuid.UUID
    ) -> Company:
        await self._check_user_in_company(company_id, user_id)
        return await self._get_company(company_id)

    async def update_company(
        self, company_id: uuid.UUID, data: dict, user_id: uuid.UUID
    ) -> Company:
        await self._check_admin(company_id, user_id)

        company = await self._get_company(company_id)

        for key, value in data.items():
            if value is not None:
                setattr(company, key, value)

        await self.session.commit()
        await self.session.refresh(company)
        return company

    async def delete_company(self, company_id: uuid.UUID, user_id: uuid.UUID):
        await self._check_admin(company_id, user_id)

        company = await self._get_company(company_id)

        from sqlalchemy import update
        await self.session.execute(
            update(User).where(User.company_id == company_id).values(company_id=None)
        )

        await self.session.delete(company)
        await self.session.commit()

    async def get_company_users(
        self,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> dict:
        await self._check_user_in_company(company_id, user_id)

        query = (
            select(
                CompanyUser,
                User,
            )
            .join(User, User.id == CompanyUser.user_id)
            .where(CompanyUser.company_id == company_id)
        )

        if search:
            query = query.where(
                User.name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%")
            )

        from sqlalchemy import func as sa_func

        count_query = query.order_by(None).subquery()
        total_items = (
            await self.session.scalar(select(sa_func.count()).select_from(count_query))
            or 0
        )

        query = query.order_by(User.name.asc())
        query = query.limit(page_size).offset((page - 1) * page_size)

        result = await self.session.execute(query)
        rows = result.all()

        from math import ceil

        items = [
            {
                "id": cu.id,
                "company_id": cu.company_id,
                "user_id": cu.user_id,
                "user_name": u.name,
                "user_email": u.email,
                "user_avatar_url": u.avatar_url,
                "user_phone": u.phone,
                "user_job_title": cu.job_title,
                "user_document": u.document,
                "user_zip_code": u.zip_code,
                "user_street": u.street,
                "user_number": u.number,
                "user_complement": u.complement,
                "user_neighborhood": u.neighborhood,
                "user_city": u.city,
                "user_state": u.state,
                "permission": cu.permission,
                "created_at": cu.created_at,
            }
            for cu, u in rows
        ]

        return PaginatedResponse(
            items=items,
            total_items=total_items,
            page=page,
            total_pages=ceil(total_items / page_size) if page_size > 0 else 1,
        )

    async def invite_user(
        self,
        company_id: uuid.UUID,
        email: str,
        permission: CompanyPermission,
        invited_by: uuid.UUID,
    ) -> CompanyInvitation:
        await self._check_admin(company_id, invited_by)

        user_res = await self.session.execute(select(User).where(User.email == email))
        user = user_res.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=404,
                detail={"error": "errorUserNotFound"},
            )

        existing = await self.session.execute(
            select(CompanyUser).where(
                CompanyUser.company_id == company_id,
                CompanyUser.user_id == user.id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail={"error": "errorUserAlreadyMember"},
            )

        pending = await self.session.execute(
            select(CompanyInvitation).where(
                CompanyInvitation.company_id == company_id,
                CompanyInvitation.user_id == user.id,
                CompanyInvitation.status == InvitationStatus.PENDING,
            )
        )
        if pending.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail={"error": "errorInvitationAlreadyPending"},
            )

        invitation = CompanyInvitation(
            company_id=company_id,
            user_id=user.id,
            invited_by=invited_by,
            permission=permission,
            status=InvitationStatus.PENDING,
        )
        self.session.add(invitation)
        await self.session.commit()
        await self.session.refresh(invitation)
        return invitation

    async def update_company_user(
        self,
        company_id: uuid.UUID,
        target_user_id: uuid.UUID,
        data: dict,
        admin_id: uuid.UUID,
    ) -> dict:
        await self._check_admin(company_id, admin_id)
        res = await self.session.execute(
            select(CompanyUser, User)
            .join(User, User.id == CompanyUser.user_id)
            .where(
                CompanyUser.company_id == company_id,
                CompanyUser.user_id == target_user_id,
            )
        )

        row = res.first()
        if not row:
            raise HTTPException(
                status_code=404, detail={"error": "errorEntityNotFound"}
            )
        company_user, user = row

        permission = data.get("permission")
        if permission is not None:
            if (
                company_user.permission == CompanyPermission.ADMIN
                and permission != CompanyPermission.ADMIN
            ):
                admins_res = await self.session.execute(
                    select(CompanyUser).where(
                        CompanyUser.company_id == company_id,
                        CompanyUser.permission == CompanyPermission.ADMIN,
                        CompanyUser.user_id != target_user_id,
                    )
                )
                has_other_admins = admins_res.scalars().first()
                if not has_other_admins:
                    raise HTTPException(
                        status_code=400,
                        detail={"error": "errorCannotHaveNoAdministrator"},
                    )
            company_user.permission = permission

        if "job_title" in data:
            company_user.job_title = data["job_title"]
        elif "user_job_title" in data:
            company_user.job_title = data["user_job_title"]

        await self.session.commit()
        await self.session.refresh(company_user)

        return {
            "id": company_user.id,
            "company_id": company_user.company_id,
            "user_id": company_user.user_id,
            "user_name": user.name,
            "user_email": user.email,
            "user_avatar_url": user.avatar_url,
            "user_phone": user.phone,
            "user_job_title": company_user.job_title,
            "user_document": user.document,
            "user_zip_code": user.zip_code,
            "user_street": user.street,
            "user_number": user.number,
            "user_complement": user.complement,
            "user_neighborhood": user.neighborhood,
            "user_city": user.city,
            "user_state": user.state,
            "permission": company_user.permission,
            "created_at": company_user.created_at,
        }

    async def update_user_permission(
        self,
        company_id: uuid.UUID,
        target_user_id: uuid.UUID,
        permission: CompanyPermission,
        admin_id: uuid.UUID,
    ):
        return await self.update_company_user(
            company_id, target_user_id, {"permission": permission}, admin_id
        )

    async def remove_me(self, company_id: uuid.UUID, user_id: uuid.UUID):
        await self._check_user_in_company(company_id, user_id)

        company_user = await self._get_company_user(company_id, user_id)

        if company_user.permission == CompanyPermission.ADMIN:
            res = await self.session.execute(
                select(CompanyUser).where(
                    CompanyUser.company_id == company_id,
                    CompanyUser.permission == CompanyPermission.ADMIN,
                    CompanyUser.user_id != user_id,
                )
            )

            has_other_admins = res.scalars().first()

            if not has_other_admins:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "errorCannotHaveNoAdministrator"},
                )

        user_res = await self.session.execute(select(User).where(User.id == user_id))
        user = user_res.scalar_one_or_none()
        if user and user.company_id == company_id:
            user.company_id = None


        await self.session.delete(company_user)
        await self.session.commit()

    async def remove_user(
        self, company_id: uuid.UUID, target_user_id: uuid.UUID, user_id: uuid.UUID
    ):
        await self._check_admin(company_id, user_id)

        if target_user_id == user_id:
            raise HTTPException(
                status_code=400,
                detail={"error": "errorCannotRemoveSelf"},
            )

        company_user = await self._get_company_user(company_id, target_user_id)

        if company_user.permission == CompanyPermission.ADMIN:
            res = await self.session.execute(
                select(CompanyUser).where(
                    CompanyUser.company_id == company_id,
                    CompanyUser.permission == CompanyPermission.ADMIN,
                    CompanyUser.user_id != target_user_id,
                )
            )
            has_other_admins = res.scalars().first()
            if not has_other_admins:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "errorCannotHaveNoAdministrator"},
                )

        user_res = await self.session.execute(
            select(User).where(User.id == target_user_id)
        )
        user = user_res.scalar_one_or_none()
        if user and user.company_id == company_id:
            user.company_id = None


        await self.session.delete(company_user)
        await self.session.commit()

    async def _get_company_user(self, company_id: uuid.UUID, user_id: uuid.UUID):
        response = await self.session.execute(
            select(CompanyUser).where(
                CompanyUser.company_id == company_id,
                CompanyUser.user_id == user_id,
            )
        )
        company_user = response.scalar_one_or_none()
        if not company_user:
            raise HTTPException(
                status_code=404, detail={"error": "errorEntityNotFound"}
            )
        return company_user

    async def get_company_invitations(
        self,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        status: InvitationStatus | None = None,
    ):
        await self._check_user_in_company(company_id, user_id)

        UserInviter = aliased(User, name="user_inviter")
        UserInvited = aliased(User, name="user_invited")

        query = (
            select(
                CompanyInvitation,
                UserInviter.name.label("invited_by_name"),
                UserInviter.email.label("invited_by_email"),
                UserInvited.name.label("user_name"),
                UserInvited.email.label("user_email"),
            )
            .join(UserInviter, CompanyInvitation.invited_by == UserInviter.id)
            .join(UserInvited, CompanyInvitation.user_id == UserInvited.id)
            .where(CompanyInvitation.company_id == company_id)
        )
        if status:
            query = query.where(CompanyInvitation.status == status)
        query = query.order_by(CompanyInvitation.created_at.desc())

        result = await self.session.execute(query)
        rows = result.all()

        return [
            {
                **row[0].model_dump(),
                "invited_by_name": row[1],
                "invited_by_email": row[2],
                "user_name": row[3],
                "user_email": row[4],
            }
            for row in rows
        ]

    async def get_user_invitations(self, user_id: uuid.UUID) -> list[dict]:
        query = (
            select(
                CompanyInvitation,
                Company.name.label("company_name"),
                User.name.label("invited_by_name"),
            )
            .join(Company, Company.id == CompanyInvitation.company_id)
            .join(User, User.id == CompanyInvitation.invited_by)
            .where(
                CompanyInvitation.user_id == user_id,
                CompanyInvitation.status == InvitationStatus.PENDING,
            )
            .order_by(CompanyInvitation.created_at.desc())
        )
        result = await self.session.execute(query)
        rows = result.all()

        return [
            {
                "id": row[0].id,
                "company_id": row[0].company_id,
                "company_name": row[1],
                "invited_by_name": row[2],
                "user_id": row[0].user_id,
                "permission": row[0].permission,
                "status": row[0].status,
                "created_at": row[0].created_at,
            }
            for row in rows
        ]

    async def accept_invitation(self, invitation_id: uuid.UUID, user_id: uuid.UUID):
        invitation = await self._get_invitation(invitation_id, user_id)

        company_user = CompanyUser(
            company_id=invitation.company_id,
            user_id=user_id,
            permission=invitation.permission,
        )
        self.session.add(company_user)

        invitation.status = InvitationStatus.ACCEPTED

        user_res = await self.session.execute(select(User).where(User.id == user_id))
        user = user_res.scalar_one_or_none()
        if user and user.company_id is None:
            user.company_id = invitation.company_id

        await self.session.commit()

    async def reject_invitation(self, invitation_id: uuid.UUID, user_id: uuid.UUID):
        invitation = await self._get_invitation(invitation_id, user_id)
        invitation.status = InvitationStatus.REJECTED
        await self.session.commit()

    async def switch_company(self, user_id: uuid.UUID, company_id: uuid.UUID) -> CompanyPermission:
        response = await self.session.execute(
            select(CompanyUser).where(
                CompanyUser.user_id == user_id,
                CompanyUser.company_id == company_id,
            )
        )
        company_user = response.scalar_one_or_none()
        if not company_user:
            raise HTTPException(
                status_code=403,
                detail={"error": "errorNotMemberOfCompany"},
            )

        user_res = await self.session.execute(select(User).where(User.id == user_id))
        user = user_res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail={"error": "errorUserNotFound"})

        user.company_id = company_id
        await self.session.commit()
        return company_user.permission

    async def cancel_invitation(
        self, company_id: uuid.UUID, invitation_id: uuid.UUID, admin_id: uuid.UUID
    ):
        await self._check_admin(company_id, admin_id)

        inv_res = await self.session.execute(
            select(CompanyInvitation).where(
                CompanyInvitation.id == invitation_id,
                CompanyInvitation.company_id == company_id,
                CompanyInvitation.status == InvitationStatus.PENDING,
            )
        )
        invitation = inv_res.scalar_one_or_none()
        if not invitation:
            raise HTTPException(
                status_code=404, detail={"error": "errorEntityNotFound"}
            )

        await self.session.delete(invitation)
        await self.session.commit()

    async def _get_invitation(
        self, invitation_id: uuid.UUID, user_id: uuid.UUID
    ) -> CompanyInvitation:
        inv_res = await self.session.execute(
            select(CompanyInvitation).where(
                CompanyInvitation.id == invitation_id,
                CompanyInvitation.user_id == user_id,
                CompanyInvitation.status == InvitationStatus.PENDING,
            )
        )
        invitation = inv_res.scalar_one_or_none()
        if not invitation:
            raise HTTPException(
                status_code=404, detail={"error": "errorEntityNotFound"}
            )

        return invitation

    async def _check_user_in_company(self, company_id: uuid.UUID, user_id: uuid.UUID):
        cu_res = await self.session.execute(
            select(CompanyUser).where(
                CompanyUser.company_id == company_id,
                CompanyUser.user_id == user_id,
            )
        )
        if not cu_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "errorInsufficientPermission"},
            )

    async def _check_admin(self, company_id: uuid.UUID, user_id: uuid.UUID):
        cu_res = await self.session.execute(
            select(CompanyUser).where(
                CompanyUser.company_id == company_id,
                CompanyUser.user_id == user_id,
                CompanyUser.permission == CompanyPermission.ADMIN,
            )
        )
        if not cu_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "errorInsufficientPermission"},
            )

    async def _get_company(self, company_id: uuid.UUID) -> Company:
        company_res = await self.session.execute(
            select(Company).where(Company.id == company_id)
        )
        company = company_res.scalar_one_or_none()
        if not company:
            raise HTTPException(
                status_code=404, detail={"error": "errorEntityNotFound"}
            )
        return company
