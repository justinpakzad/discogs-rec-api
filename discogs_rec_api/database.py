from discogs_rec_api.config import Config
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator


def create_engine(database_url):
    """
    Create async SQLAlchemy engine.

    Returns:
        AsyncEngine: Configured async SQLAlchemy engine
    """
    return create_async_engine(database_url, echo=False)


def create_async_session(async_engine):
    """
    Create async session maker.

    Args:
        async_engine: Async SQLAlchemy engine

    Returns:
        async_sessionmaker: Factory for creating async database sessions
    """
    return async_sessionmaker(async_engine, expire_on_commit=False)


settings = Config()
# global instances
async_engine = create_engine(settings.database_url)
async_session = create_async_session(async_engine)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides database sessions.

    Yields:
        AsyncSession: Database session for the current request
    """
    async with async_session() as session:
        yield session


# async def create_tables():
#     """Create all database tables from SQLAlchemy models."""
#     async with async_engine.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all)
#         # await conn.run_sync(Base.metadata.create_all)
