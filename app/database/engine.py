from app.config import settings
import asyncio
import asyncpg
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import async_sessionmaker

engine = create_async_engine(url=settings.POSTGRES_URL, echo=settings.DEBUG)

async_session_factory = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)


async def create_database_tables():
    for attempt in range(5):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            print("Database tables created")
            break
        except (
            OperationalError,
            ConnectionRefusedError,
            asyncpg.exceptions.CannotConnectNowError,
        ) as e:
            print(f"Error ({e}) Database not ready, retrying...")
            await asyncio.sleep(5)


async def get_session():
    async with async_session_factory() as session:
        yield session
