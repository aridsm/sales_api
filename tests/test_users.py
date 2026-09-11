import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_user_signup_and_login(unauth_client: AsyncClient):
    # Unique email for testing signup
    test_email = f"newuser_{uuid.uuid4()}@example.com"
    test_password = "strongpassword123"

    # 1. Signup
    signup_response = await unauth_client.post("/users/signup", json={
        "name": "New User",
        "email": test_email,
        "password": test_password
    })
    
    assert signup_response.status_code == 201
    data = signup_response.json()
    assert data["email"] == test_email
    assert data["name"] == "New User"
    assert "id" in data

    # 2. Login
    # The /login route uses OAuth2PasswordRequestForm, which expects form data, not JSON
    login_response = await unauth_client.post("/users/login", data={
        "username": test_email,
        "password": test_password
    })
    
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, test_user):
    # Since we use `client`, it is already authenticated as `test_user`
    me_response = await client.get("/users/me")
    assert me_response.status_code == 200
    
    me_data = me_response.json()
    assert me_data["email"] == test_user.email
    assert me_data["name"] == test_user.name
    assert me_data["id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_access_protected_routes_without_active_company(unauth_client: AsyncClient, session):
    from app.database.models.user import User
    from app.api.dependencies import get_user_logged
    from app.api.schemas.user import UserResponse
    from app.main import app
    from datetime import datetime

    user_id = uuid.uuid4()
    db_user = User(
        id=user_id,
        name="No Company User",
        email=f"nocompany_{user_id}@example.com",
        password_hash="hashed_password",
        company_id=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    user_no_company = UserResponse(
        id=user_id,
        email=db_user.email,
        name=db_user.name,
        company_id=None,
        permission=None,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )

    app.dependency_overrides[get_user_logged] = lambda: user_no_company

    endpoints = [
        "/categories/",
        "/categories/amounts",
        "/products/",
        "/sales/",
        "/sale_products/",
        "/other_expenses/",
        "/stock_entries/",
        "/stock_entry_products/",
        "/dashboard/chart",
        "/dashboard/budgets",
        "/history/",
    ]

    for endpoint in endpoints:
        res = await unauth_client.get(endpoint)
        assert res.status_code == 403, f"Endpoint {endpoint} returned {res.status_code} instead of 403: {res.text}"
        assert res.json() == {"detail": {"error": "errorUserHasNoActiveCompany"}}
