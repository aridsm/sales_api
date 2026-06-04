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
