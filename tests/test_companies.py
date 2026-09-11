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


