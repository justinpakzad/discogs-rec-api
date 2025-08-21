import os
import pytest
import psycopg2
import csv
import pytest_asyncio
from pathlib import Path
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from discogs_rec_api.main import app
from discogs_rec_api.database import get_db
from discogs_rec_api.models import Base
from discogs_rec_api.config import Config
from discogs_rec_api.database import create_engine, create_async_session
from discogs_rec_api.security import create_access_token
from discogs_rec_api.security import get_password_hash
from discogs_rec_api.models import Users

os.environ["TESTING"] = "true"


@pytest.fixture(scope="session")
def test_settings():
    test_settings = Config()
    return test_settings


@pytest.fixture
def urls():
    return [
        "https://www.discogs.com/release/335130-FL-Untitled",
        "https://www.discogs.com/release/926397",
    ]


@pytest.fixture
async def test_users(test_engine):
    async_session = create_async_session(test_engine)
    async with async_session() as session:
        users = {}
        for username in ["testuser", "testuser2"]:
            res = await session.execute(
                text("select id from users where username = :username"),
                {"username": username},
            )
            users[username] = res.scalar()
    return users


@pytest.fixture
async def deletable_user(test_engine):
    async_session = create_async_session(test_engine)
    async with async_session() as session:
        user = Users(
            username="deleteuser",
            email="deleteme@example.com",
            hashed_password=get_password_hash("testpassword123"),
            is_superuser=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    print(user.id)
    return user.id


@pytest.fixture
async def cleanup_user_recs(test_engine):
    async_session = create_async_session(test_engine)
    async with async_session() as session:
        await session.execute(text("delete from feedback where 1=1 "))  # Delete first
        await session.execute(text("delete from recommendations where 1=1 "))
        await session.execute(
            text("delete from searches where 1=1 ")
        )  # Delete after feedback
        await session.execute(text("delete from favorites where 1=1 "))
        await session.commit()


@pytest.fixture
def user_token_headers():
    token = create_access_token(data={"sub": "testuser"})
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    return headers


@pytest.fixture
def superuser_token_headers():
    token = create_access_token(data={"sub": "superuser"})
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    return headers


@pytest.fixture
def test_engine(test_settings):
    engine = create_engine(test_settings.database_url)
    return engine


@pytest.fixture(scope="session")
def session_engine(test_settings):
    return create_engine(test_settings.database_url)


@pytest.fixture(scope="session")
async def setup_test_database(session_engine):
    async with session_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


def load_releases_from_csv(test_settings):
    csv_path = Path(__file__).parents[1] / "test_data" / "test_releases.csv"
    conn = psycopg2.connect(test_settings.sync_database_url)
    curr = conn.cursor()
    with open(csv_path, "r") as f:
        csv_reader = csv.DictReader(f)
        cols = csv_reader.fieldnames
        columns = ", ".join(cols)

        f.seek(0)

        sql = f"""
            COPY releases ({columns})
            FROM STDIN
            WITH (FORMAT CSV, HEADER TRUE, QUOTE '"')
        """
        curr.copy_expert(sql, f)

    curr.close()
    conn.commit()
    conn.close()


async def create_test_users(session_engine):

    async_session = create_async_session(session_engine)
    async with async_session() as db:
        # regular user
        regular_user = Users(
            username="testuser",
            email="testuser@example.com",
            hashed_password=get_password_hash("testpassword123"),
            is_superuser=False,
        )
        regular_user_2 = Users(
            username="testuser2",
            email="testuser2@example.com",
            hashed_password=get_password_hash("testpassword1222"),
            is_superuser=False,
        )

        # super user
        super_user = Users(
            username="superuser",
            email="superuser@super.com",
            hashed_password=get_password_hash("superpassword123"),
            is_superuser=True,
        )

        db.add(regular_user)
        db.add(regular_user_2)
        db.add(super_user)
        await db.commit()


@pytest.fixture(scope="session")
def seed_releases(test_settings, setup_test_database):
    load_releases_from_csv(test_settings)


@pytest.fixture(scope="session")
async def seed_users(session_engine, setup_test_database):
    await create_test_users(session_engine)


@pytest.fixture(scope="session", autouse=True)
def prepare_all_data(seed_releases, seed_users):
    pass


@pytest_asyncio.fixture(scope="session")
async def app_with_lifespan():
    async with app.router.lifespan_context(app):
        yield app


@pytest_asyncio.fixture
async def client(test_engine, app_with_lifespan):
    async def override_get_db():
        async_session = create_async_session(test_engine)
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app_with_lifespan), base_url="http://test"
    ) as test_client:
        yield test_client
