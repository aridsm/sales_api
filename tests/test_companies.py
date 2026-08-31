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
