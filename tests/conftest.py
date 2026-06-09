from typing import AsyncGenerator, Any
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from starlette.testclient import TestClient
import settings
import os
import asyncio
from db.session import get_db
from main import app
import asyncpg


# create async engine for interaction with db
test_engine = create_async_engine(settings.TEST_DATABASE_URL, future=True, echo=True)

# create session maker for interaction with db
test_async_session = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

CLEAN_TABLES = [
    'users',
]

@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope='session', autouse=True)
async def run_migrations():
    os.system('alembic init migrations')
    os.system('alembic revision --autogenerate -m "test running migrations')
    os.system('alembic upgrade head')

@pytest.fixture(scope='session')
async def async_session_test():
    engine = create_async_engine(settings.TEST_DATABASE_URL, future=True, echo=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield async_session

@pytest.fixture(scope='function', autouse=True)
async def clean_tables(async_session_test):
    """Clean tables before each test."""
    async with async_session_test() as session:
        async with session.begin():
            for table in CLEAN_TABLES:
                await session.execute(f"""TRUNCATE TABLE {table} CASCADE;""")


async def _get_test_db():
    try:
        yield test_async_session()
    finally:
        pass

@pytest.fixture(scope='function')
async def client() -> AsyncGenerator[TestClient, Any, None]:
    """
    create a new FastAPI TestClient that uses the 'db_session' fixture to override
    the 'get_db' dependency that is injected into routers.
    """

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope='session')
async def asyncpg_pool():
    pool = await asyncpg.create_pool("".join(settings.TEST_DATABASE_URL.split("+asyncpg")))
    yield pool
    pool.close()

@pytest.fixture
async def get_user_from_db(asyncpg_pool):

    async def get_user_from_db_by_uuid(user_id: str):
        async with asyncpg_pool.acquire() as connection:
            return await connection.fetch("""SELECT * FROM users WHERE user_id = $1""", user_id)
    return get_user_from_db_by_uuid