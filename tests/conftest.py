import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import pool
from sqlmodel import SQLModel
import os
from typing import AsyncGenerator
from datetime import datetime
import uuid

# Override database config before importing any app modules
os.environ["DB_HOST"] = os.environ.get("DB_TEST_HOST", "localhost")
os.environ["DB_PORT"] = os.environ.get("DB_TEST_PORT", "5433")
os.environ["DB_NAME"] = os.environ.get("DB_TEST_NAME", "sales_api_test")

from app.main import app
from app.config import settings
from app.database.engine import get_session
from app.api.dependencies import get_user_logged
from app.api.schemas.user import UserResponse

TEST_POSTGRES_URL = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"

engine_test = create_async_engine(TEST_POSTGRES_URL, echo=False, poolclass=pool.NullPool)
async_session_factory_test = async_sessionmaker(
    bind=engine_test, expire_on_commit=False, class_=AsyncSession
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

@pytest_asyncio.fixture
async def session() -> AsyncSession:
    return async_session_factory_test()

@pytest_asyncio.fixture
async def test_user(session: AsyncSession):
    from app.database.models.user import User
    from app.database.models.company import Company
    from app.database.models.company_user import CompanyUser
    from app.enums.company import CompanyPermission
    import uuid
    from datetime import datetime

    company_id = uuid.uuid4()
    company = Company(
        id=company_id,
        name="Test Company",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(company)
    await session.flush()

    user_id = uuid.uuid4()
    user_email = f"test_{user_id}@example.com"
    db_user = User(
        id=user_id,
        name="Test User",
        email=user_email,
        password_hash="hashed_password",
        company_id=company_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(db_user)
    await session.flush()

    company_user = CompanyUser(
        company_id=company_id,
        user_id=user_id,
        permission=CompanyPermission.ADMIN,
        created_at=datetime.utcnow()
    )
    session.add(company_user)

    await session.commit()
    await session.refresh(db_user)

    return UserResponse(
        id=user_id,
        email=user_email,
        name="Test User",
        company_id=company_id,
        permission=CompanyPermission.ADMIN,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )

@pytest_asyncio.fixture
async def client(test_user: UserResponse, request) -> AsyncClient:
    async def override_get_user_logged():
        return test_user
        
    async def override_get_session():
        async with async_session_factory_test() as session:
            yield session

    app.dependency_overrides[get_user_logged] = override_get_user_logged
    app.dependency_overrides[get_session] = override_get_session

    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    c = AsyncClient(transport=transport, base_url="http://test")
    
    def teardown():
        app.dependency_overrides.clear()
        
    request.addfinalizer(teardown)
    return c

@pytest_asyncio.fixture
async def unauth_client(request) -> AsyncClient:
    async def override_get_session():
        async with async_session_factory_test() as session:
            yield session
    
    app.dependency_overrides[get_session] = override_get_session

    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    c = AsyncClient(transport=transport, base_url="http://test")
    
    def teardown():
        app.dependency_overrides.clear()
        
    request.addfinalizer(teardown)
    return c
