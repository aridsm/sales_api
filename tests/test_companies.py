import pytest
from httpx import AsyncClient
import uuid
from fastapi import status
from app.database.models.user import User
from app.database.models.company_user import CompanyUser
from app.enums.company import CompanyPermission
from datetime import datetime
from tests.conftest import async_session_factory_test

@pytest.mark.asyncio
async def test_remove_me_only_admin_fails(client: AsyncClient, test_user):
    # test_user is the only admin of their company (created in conftest.py)
    response = await client.delete(f"/companies/{test_user.company_id}/users/me")
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "errorCannotHaveNoAdministrator"

@pytest.mark.asyncio
async def test_remove_me_with_other_admin_succeeds(client: AsyncClient, test_user):
    # Create another admin in the same company
    other_user_id = uuid.uuid4()
    
    async with async_session_factory_test() as session:
        other_db_user = User(
            id=other_user_id,
            name="Other Admin",
            email=f"other_{other_user_id}@example.com",
            password_hash="hashed",
            company_id=test_user.company_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(other_db_user)
        await session.flush()
        
        other_company_user = CompanyUser(
            company_id=test_user.company_id,
            user_id=other_user_id,
            permission=CompanyPermission.ADMIN,
            created_at=datetime.utcnow()
        )
        session.add(other_company_user)
        await session.commit()
    
    # Now trying to remove me should succeed since there is another admin
    response = await client.delete(f"/companies/{test_user.company_id}/users/me")
    assert response.status_code == 204

@pytest.mark.asyncio
async def test_remove_user_self_removal_fails(client: AsyncClient, test_user):
    # Trying to remove self via remove_user endpoint should fail
    response = await client.delete(f"/companies/{test_user.company_id}/users/{test_user.id}")
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "errorCannotRemoveSelf"

@pytest.mark.asyncio
async def test_remove_other_user_succeeds(client: AsyncClient, test_user):
    # Create a member in the company
    member_user_id = uuid.uuid4()
    
    async with async_session_factory_test() as session:
        member_db_user = User(
            id=member_user_id,
            name="Member User",
            email=f"member_{member_user_id}@example.com",
            password_hash="hashed",
            company_id=test_user.company_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(member_db_user)
        await session.flush()
        
        member_company_user = CompanyUser(
            company_id=test_user.company_id,
            user_id=member_user_id,
            permission=CompanyPermission.VIEW,
            created_at=datetime.utcnow()
        )
        session.add(member_company_user)
        await session.commit()

    # Admin removes the member user
    response = await client.delete(f"/companies/{test_user.company_id}/users/{member_user_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_remove_me_with_multiple_other_admins_succeeds(client: AsyncClient, test_user):
    # Create two other admins in the same company
    admin2_id = uuid.uuid4()
    admin3_id = uuid.uuid4()

    async with async_session_factory_test() as session:
        for a_id, a_name in [(admin2_id, "Admin 2"), (admin3_id, "Admin 3")]:
            user_obj = User(
                id=a_id,
                name=a_name,
                email=f"admin_{a_id}@example.com",
                password_hash="hashed",
                company_id=test_user.company_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(user_obj)
            await session.flush()

            comp_user = CompanyUser(
                company_id=test_user.company_id,
                user_id=a_id,
                permission=CompanyPermission.ADMIN,
                created_at=datetime.utcnow(),
            )
            session.add(comp_user)
        await session.commit()

    # When there are multiple other admins, remove_me must not crash with MultipleResultsFound
    response = await client.delete(f"/companies/{test_user.company_id}/users/me")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_remove_user_preserves_created_by(client: AsyncClient, test_user):
    from app.database.models.category import Category
    from app.enums.category import CategoryType

    member_id = uuid.uuid4()
    cat_id = uuid.uuid4()

    async with async_session_factory_test() as session:
        member_user = User(
            id=member_id,
            name="Author User",
            email=f"author_{member_id}@example.com",
            password_hash="hashed",
            company_id=test_user.company_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(member_user)
        await session.flush()

        member_cu = CompanyUser(
            company_id=test_user.company_id,
            user_id=member_id,
            permission=CompanyPermission.VIEW_EDIT,
            created_at=datetime.utcnow(),
        )
        session.add(member_cu)

        # Create category with created_by = member_id
        cat = Category(
            id=cat_id,
            name="Member Category",
            type=CategoryType.PRODUCT,
            user_id=member_id,
            created_by=member_id,
            company_id=test_user.company_id,
            created_at=datetime.utcnow(),
        )
        session.add(cat)
        await session.commit()

    # Verify created_by before removal
    get_cat = await client.get(f"/categories/{cat_id}")
    assert get_cat.status_code == 200
    assert get_cat.json()["created_by"] == str(member_id)
    assert get_cat.json()["created_by_name"] == "Author User"
    assert get_cat.json()["created_by_email"] == f"author_{member_id}@example.com"

    # Remove the member from the company
    del_res = await client.delete(f"/companies/{test_user.company_id}/users/{member_id}")
    assert del_res.status_code == 204

    # Verify created_by, created_by_name and created_by_email are preserved
    get_cat_after = await client.get(f"/categories/{cat_id}")
    assert get_cat_after.status_code == 200
    assert get_cat_after.json()["created_by"] == str(member_id)
    assert get_cat_after.json()["created_by_name"] == "Author User"
    assert get_cat_after.json()["created_by_email"] == f"author_{member_id}@example.com"


@pytest.mark.asyncio
async def test_get_company_by_id(client: AsyncClient, test_user):
    res = await client.get(f"/companies/{test_user.company_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == str(test_user.company_id)
    assert data["name"] == "Test Company"


@pytest.mark.asyncio
async def test_update_company_by_admin(client: AsyncClient, test_user):
    update_data = {
        "name": "Updated Company Name",
        "document": "12.345.678/0001-90",
        "email": "contact@company.com",
        "phone": "+551133334444",
        "website": "https://company.com",
        "zip_code": "01310-200",
        "street": "Avenida Brigadeiro Faria Lima",
        "number": "2000",
        "complement": "10º Andar",
        "neighborhood": "Pinheiros",
        "city": "São Paulo",
        "state": "SP",
    }
    res = await client.patch(f"/companies/{test_user.company_id}", json=update_data)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Updated Company Name"
    assert data["document"] == "12.345.678/0001-90"
    assert data["email"] == "contact@company.com"
    assert data["phone"] == "+551133334444"
    assert data["website"] == "https://company.com"
    assert data["city"] == "São Paulo"


@pytest.mark.asyncio
async def test_update_company_by_non_admin_fails(unauth_client: AsyncClient, test_user):
    from app.api.dependencies import get_user_logged
    from app.api.schemas.user import UserResponse
    from app.main import app

    view_user = UserResponse(
        id=uuid.uuid4(),
        email="view_user@example.com",
        name="View User",
        company_id=test_user.company_id,
        permission=CompanyPermission.VIEW,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    try:
        app.dependency_overrides[get_user_logged] = lambda: view_user
        res = await unauth_client.patch(f"/companies/{test_user.company_id}", json={"name": "Hacked"})
        assert res.status_code == 403
        assert res.json()["detail"]["error"] == "errorInsufficientPermission"
    finally:
        app.dependency_overrides.pop(get_user_logged, None)


@pytest.mark.asyncio
async def test_upload_company_logo_by_admin(client: AsyncClient, test_user):
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    files = {"file": ("logo.png", fake_png, "image/png")}

    res = await client.post(f"/companies/{test_user.company_id}/logo", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["logo_url"] is not None
    assert "/static/uploads/company-logos/" in data["logo_url"]


@pytest.mark.asyncio
async def test_upload_company_logo_by_non_admin_fails(unauth_client: AsyncClient, test_user):
    from app.api.dependencies import get_user_logged
    from app.api.schemas.user import UserResponse
    from app.main import app

    view_user = UserResponse(
        id=uuid.uuid4(),
        email="view_user_logo@example.com",
        name="View User",
        company_id=test_user.company_id,
        permission=CompanyPermission.VIEW,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    try:
        app.dependency_overrides[get_user_logged] = lambda: view_user
        fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
        files = {"file": ("logo.png", fake_png, "image/png")}

        res = await unauth_client.post(f"/companies/{test_user.company_id}/logo", files=files)
        assert res.status_code == 403
        assert res.json()["detail"]["error"] == "errorInsufficientPermission"
    finally:
        app.dependency_overrides.pop(get_user_logged, None)


@pytest.mark.asyncio
async def test_get_company_users_includes_profile_fields(client: AsyncClient, test_user):
    # Update profile of test_user
    await client.patch("/users/me", json={
        "phone": "+5511988887777",
        "document": "999.888.777-66",
        "city": "Campinas",
        "state": "SP",
    })

    # Update job_title on company_user
    await client.patch(f"/companies/{test_user.company_id}/users/{test_user.id}", json={
        "job_title": "CTO",
    })

    # Fetch company users
    res = await client.get(f"/companies/{test_user.company_id}/users")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 1

    user_item = next(item for item in data["items"] if item["user_id"] == str(test_user.id))
    assert user_item["user_job_title"] == "CTO"
    assert user_item["user_phone"] == "+5511988887777"
    assert user_item["user_document"] == "999.888.777-66"
    assert user_item["user_city"] == "Campinas"
    assert user_item["user_state"] == "SP"
    assert "job_title" not in user_item
    assert "phone" not in user_item
    assert "document" not in user_item


@pytest.mark.asyncio
async def test_admin_can_update_member_job_title(client: AsyncClient, test_user):
    # Create a member in the company
    member_user_id = uuid.uuid4()
    async with async_session_factory_test() as session:
        member_db_user = User(
            id=member_user_id,
            name="Developer User",
            email=f"dev_{member_user_id}@example.com",
            password_hash="hashed",
            company_id=test_user.company_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(member_db_user)
        await session.flush()

        member_cu = CompanyUser(
            company_id=test_user.company_id,
            user_id=member_user_id,
            permission=CompanyPermission.VIEW_EDIT,
            job_title="Junior Dev",
            created_at=datetime.utcnow(),
        )
        session.add(member_cu)
        await session.commit()

    # Admin updates the member's job_title
    patch_res = await client.patch(
        f"/companies/{test_user.company_id}/users/{member_user_id}",
        json={"job_title": "Senior Engineer"}
    )
    assert patch_res.status_code == 200
    patch_data = patch_res.json()
    assert patch_data["user_job_title"] == "Senior Engineer"
    assert patch_data["user_name"] == "Developer User"

    # Verify via get company users
    res = await client.get(f"/companies/{test_user.company_id}/users")
    assert res.status_code == 200
    member_item = next(item for item in res.json()["items"] if item["user_id"] == str(member_user_id))
    assert member_item["user_job_title"] == "Senior Engineer"


@pytest.mark.asyncio
async def test_non_admin_cannot_update_member_job_title(unauth_client: AsyncClient, test_user):
    from app.api.dependencies import get_user_logged
    from app.api.schemas.user import UserResponse
    from app.main import app

    view_user = UserResponse(
        id=uuid.uuid4(),
        email="view_user_edit@example.com",
        name="View User",
        company_id=test_user.company_id,
        permission=CompanyPermission.VIEW,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    try:
        app.dependency_overrides[get_user_logged] = lambda: view_user
        res = await unauth_client.patch(
            f"/companies/{test_user.company_id}/users/{test_user.id}",
            json={"job_title": "Hacked Title"}
        )
        assert res.status_code == 403
        assert res.json()["detail"]["error"] == "errorInsufficientPermission"
    finally:
        app.dependency_overrides.pop(get_user_logged, None)


@pytest.mark.asyncio
async def test_get_my_companies_includes_all_fields(client: AsyncClient, test_user):
    # Update company details
    update_data = {
        "document": "11.222.333/0001-44",
        "email": "contato@empresa.com",
        "phone": "+5585999998888",
        "website": "https://minhaempresa.com",
        "zip_code": "60000-000",
        "street": "Avenida Beira Mar",
        "number": "100",
        "complement": "Sala 10",
        "neighborhood": "Meireles",
        "city": "Fortaleza",
        "state": "CE",
    }
    patch_res = await client.patch(f"/companies/{test_user.company_id}", json=update_data)
    assert patch_res.status_code == 200

    # Get companies list
    res = await client.get("/companies/")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 1

    company_item = next(c for c in data["items"] if c["id"] == str(test_user.company_id))
    assert company_item["name"] == "Test Company"
    assert company_item["document"] == "11.222.333/0001-44"
    assert company_item["email"] == "contato@empresa.com"
    assert company_item["phone"] == "+5585999998888"
    assert company_item["website"] == "https://minhaempresa.com"
    assert company_item["zip_code"] == "60000-000"
    assert company_item["street"] == "Avenida Beira Mar"
    assert company_item["number"] == "100"
    assert company_item["complement"] == "Sala 10"
    assert company_item["neighborhood"] == "Meireles"
    assert company_item["city"] == "Fortaleza"
    assert company_item["state"] == "CE"
    assert company_item["permission"] == CompanyPermission.ADMIN.value
    assert "created_at" in company_item
    assert "updated_at" in company_item


@pytest.mark.asyncio
async def test_cancel_invitation(client: AsyncClient, test_user):
    # Create another user to invite
    invitee_id = uuid.uuid4()
    async with async_session_factory_test() as session:
        invitee = User(
            id=invitee_id,
            name="Invitee",
            email=f"invitee_{invitee_id}@example.com",
            password_hash="hashed",
            company_id=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(invitee)
        await session.commit()

    # Invite user
    inv_res = await client.post(
        f"/companies/{test_user.company_id}/users",
        json={"email": f"invitee_{invitee_id}@example.com", "permission": 1},
    )
    assert inv_res.status_code == 201
    invitation_id = inv_res.json()["id"]

    # Cancel invitation
    del_res = await client.delete(
        f"/companies/{test_user.company_id}/invitations/{invitation_id}"
    )
    assert del_res.status_code == 204

    # Invitations list should now be empty
    list_res = await client.get(f"/companies/{test_user.company_id}/invitations")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 0


@pytest.mark.asyncio
async def test_delete_company_clears_company_id_for_all_users(client: AsyncClient, test_user):
    from sqlmodel import select
    # Create another user belonging to this company
    member_id = uuid.uuid4()
    async with async_session_factory_test() as session:
        member = User(
            id=member_id,
            name="Member to clear",
            email=f"clear_{member_id}@example.com",
            password_hash="hashed",
            company_id=test_user.company_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(member)
        await session.commit()

    # Delete company
    del_res = await client.delete(f"/companies/{test_user.company_id}")
    assert del_res.status_code == 204

    # Check both users have company_id == None
    async with async_session_factory_test() as session:
        u1 = (await session.execute(select(User).where(User.id == test_user.id))).scalar_one()
        u2 = (await session.execute(select(User).where(User.id == member_id))).scalar_one()
        assert u1.company_id is None
        assert u2.company_id is None




