import pytest
from discogs_rec_api.database import create_async_session
from sqlalchemy import text


@pytest.mark.asyncio
async def test_seed_data_loaded(test_engine):
    async_session = create_async_session(test_engine)
    async with async_session() as session:
        res = await session.execute(text("select count(*) from releases"))
        count = res.scalar()

        assert count >= 5

        res = await session.execute(text("select count(*) from users"))
        count = res.scalar()
        assert count >= 2
