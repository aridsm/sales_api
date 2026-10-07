import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_user_signup_and_login(unauth_client: AsyncClient, session):
    from app.database.models.user import User
    from app.services.user import UserService
    from sqlmodel import select

    # Unique email for testing signup
    test_email = f"newuser_{uuid.uuid4()}@example.com"
    test_password = "strongpassword123"

    # 1. Signup
    signup_response = await unauth_client.post(
        "/users/signup",
        json={
            "name": "New User",
            "email": test_email,
            "password": test_password,
        },
    )

    assert signup_response.status_code == 201
    data = signup_response.json()
    assert data["email"] == test_email
    assert data["is_verified"] is False
    assert "message" in data

    # 2. Login BEFORE verification should be rejected with 403
    unverified_login_response = await unauth_client.post(
        "/users/login",
        data={
            "username": test_email,
            "password": test_password,
        },
    )
    assert unverified_login_response.status_code == 403
    assert unverified_login_response.json()["detail"]["error"] == "errorEmailNotVerified"

    # Retrieve user from DB to get the stored token hash
    query = select(User).where(User.email == test_email)
    user = (await session.execute(query)).scalar_one()
    assert user.verification_token is not None
    assert len(user.verification_token) == 64  # SHA-256 hex digest length

    # For testing, generate a known token & hash to test verify-email endpoint
    raw_token = "test_raw_verification_token_12345"
    user.verification_token = UserService.hash_token(raw_token)
    await session.commit()

    # 3. Verify Email with invalid token
    invalid_verify_res = await unauth_client.post(
        "/users/verify-email",
        json={"token": "wrong_token_value"},
    )
    assert invalid_verify_res.status_code == 400
    assert invalid_verify_res.json()["detail"]["error"] == "errorInvalidOrExpiredVerificationToken"

    # 4. Verify Email with valid token
    verify_res = await unauth_client.post(
        "/users/verify-email",
        json={"token": raw_token},
    )
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert "access_token" in verify_data
    assert "refresh_token" in verify_data

    # Token should be consumed (one-time use)
    await session.refresh(user)
    assert user.is_verified is True
    assert user.verification_token is None

    # 5. Login AFTER verification should succeed
    login_response = await unauth_client.post(
        "/users/login",
        data={
            "username": test_email,
            "password": test_password,
        },
    )

    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_resend_verification_endpoint(unauth_client: AsyncClient, session):
    from app.database.models.user import User
    from sqlmodel import select

    # Create unverified user
    user_id = uuid.uuid4()
    test_email = f"resend_{user_id}@example.com"
    await unauth_client.post(
        "/users/signup",
        json={
            "name": "Resend Test",
            "email": test_email,
            "password": "password123",
        },
    )

    # Call resend verification
    resend_res = await unauth_client.post(
        "/users/resend-verification",
        json={"email": test_email},
    )
    assert resend_res.status_code == 200
    assert "message" in resend_res.json()

    # Verify that the verification token in DB is a 64-char SHA-256 hash
    query = select(User).where(User.email == test_email)
    user = (await session.execute(query)).scalar_one()
    assert user.verification_token is not None
    assert len(user.verification_token) == 64


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

    try:
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
    finally:
        app.dependency_overrides.pop(get_user_logged, None)


@pytest.mark.asyncio
async def test_update_user_profile(client: AsyncClient, test_user):
    update_data = {
        "name": "Updated Name",
        "phone": "+5511999998888",
        "job_title": "Software Engineer",
        "document": "123.456.789-00",
        "zip_code": "01310-100",
        "street": "Avenida Paulista",
        "number": "1000",
        "complement": "Apto 42",
        "neighborhood": "Bela Vista",
        "city": "São Paulo",
        "state": "SP",
    }
    res = await client.patch("/users/me", json=update_data)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Updated Name"
    assert data["phone"] == "+5511999998888"
    assert data["job_title"] == "Software Engineer"
    assert data["document"] == "123.456.789-00"
    assert data["zip_code"] == "01310-100"
    assert data["street"] == "Avenida Paulista"
    assert data["city"] == "São Paulo"
    assert data["state"] == "SP"

    # Verify via GET /users/me
    get_res = await client.get("/users/me")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["phone"] == "+5511999998888"
    assert get_data["job_title"] == "Software Engineer"


@pytest.mark.asyncio
async def test_change_password_success(client: AsyncClient, unauth_client: AsyncClient, test_user):
    # Change password
    res = await client.post("/users/change-password", json={
        "current_password": "password123",
        "new_password": "new_secure_password_456"
    })
    assert res.status_code == 204

    # Try logging in with the new password
    login_res = await unauth_client.post("/users/login", data={
        "username": test_user.email,
        "password": "new_secure_password_456"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


@pytest.mark.asyncio
async def test_change_password_invalid_current(client: AsyncClient, test_user):
    res = await client.post("/users/change-password", json={
        "current_password": "wrong_old_password",
        "new_password": "new_secure_password_456"
    })
    assert res.status_code == 400
    assert res.json()["detail"]["error"] == "errorInvalidCurrentPassword"


@pytest.mark.asyncio
async def test_upload_my_avatar(client: AsyncClient, test_user):
    # Create fake image bytes
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    files = {"file": ("avatar.png", fake_png, "image/png")}

    res = await client.post("/users/me/avatar", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["avatar_url"] is not None
    assert "/static/uploads/avatars/" in data["avatar_url"]


@pytest.mark.asyncio
async def test_change_password_rate_limit(client: AsyncClient, test_user):
    for _ in range(5):
        await client.post(
            "/users/change-password",
            json={
                "current_password": "wrong_password",
                "new_password": "new_secure_password_456",
            },
        )

    res = await client.post(
        "/users/change-password",
        json={
            "current_password": "wrong_password",
            "new_password": "new_secure_password_456",
        },
    )
    assert res.status_code == 429
    assert res.json()["detail"]["error"] == "errorRateLimitExceeded"


@pytest.mark.asyncio
async def test_email_change_flow(client: AsyncClient, unauth_client: AsyncClient, session, test_user):
    from app.services.user import UserService
    from app.database.redis import redis_db
    import json

    new_email = f"new_email_{uuid.uuid4()}@example.com"

    # 1. Invalid current password (long and short)
    res = await client.post(
        "/users/request-email-change",
        json={
            "new_email": new_email,
            "password": "wrong_password_123",
        },
    )
    assert res.status_code == 400
    assert res.json()["detail"]["error"] == "errorInvalidCurrentPassword"

    res_short = await client.post(
        "/users/request-email-change",
        json={
            "new_email": new_email,
            "password": "12345",
        },
    )
    assert res_short.status_code == 400
    assert res_short.json()["detail"]["error"] == "errorInvalidCurrentPassword"

    # 2. Same email
    res = await client.post(
        "/users/request-email-change",
        json={
            "new_email": test_user.email,
            "password": "password123",
        },
    )
    assert res.status_code == 400
    assert res.json()["detail"]["error"] == "errorEmailSameAsCurrent"

    # 3. Successful request
    res = await client.post(
        "/users/request-email-change",
        json={
            "new_email": new_email,
            "password": "password123",
        },
    )
    assert res.status_code == 200
    assert "message" in res.json()

    # In test environment, let's create a known token in redis to confirm
    raw_token = "test_email_change_token_999"
    token_hash = UserService.hash_token(raw_token)
    payload = json.dumps({"user_id": str(test_user.id), "new_email": new_email})
    await redis_db.set_value(f"email_change:{token_hash}", payload, 3600)

    # 4. Invalid confirm token
    res = await unauth_client.post(
        "/users/confirm-email-change",
        json={"token": "invalid_token"},
    )
    assert res.status_code == 400
    assert res.json()["detail"]["error"] == "errorInvalidOrExpiredVerificationToken"

    # 5. Valid confirm token
    res = await unauth_client.post(
        "/users/confirm-email-change",
        json={"token": raw_token},
    )
    assert res.status_code == 200
    token_data = res.json()
    assert "access_token" in token_data

    # 6. Login with new email should succeed
    login_res = await unauth_client.post(
        "/users/login",
        data={
            "username": new_email,
            "password": "password123",
        },
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

