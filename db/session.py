from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

import settings

########################################
# BLOCK FOR COMMON INTERACTION WITH DB #
########################################

# create async engine for interaction with db
engine = create_async_engine(settings.REAL_DATABASE_URL, future=True, echo=True)

# create session maker for interaction with db
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator:
    try:
        session: AsyncSession = async_session()
        yield session
    finally:
        await session.close()
