import pytest
from discogs_rec_api.database import create_async_session
from sqlalchemy import select
from discogs_rec_api.models import Favorites


@pytest.mark.asyncio
async def test_add_to_favorite(client, user_token_headers, cleanup_user_recs):
    response = await client.post(
        "/user/me/favorites/926397",
        headers=user_token_headers,
    )

    assert response.status_code == 201
    assert response.json().get("release_id") == 926397


@pytest.mark.asyncio
async def test_delete_favorite(
    client, test_engine, user_token_headers, test_users, cleanup_user_recs
):
    response = await client.post(
        "/user/me/favorites/926397",
        headers=user_token_headers,
    )

    assert response.status_code == 201
    assert response.json().get("release_id") == 926397

    response = await client.delete(
        "/user/me/favorites/926397",
        headers=user_token_headers,
    )
    assert response.status_code == 204
    async_session = create_async_session(test_engine)
    async with async_session() as session:
        res = await session.execute(
            select(Favorites).where(
                (Favorites.release_id == 926397)
                & (Favorites.user_id == test_users.get("testuser"))
            )
        )
        assert res.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_favorite_already_exist(client, user_token_headers, cleanup_user_recs):
    response = await client.post(
        "/user/me/favorites/926397",
        headers=user_token_headers,
    )

    assert response.status_code == 201
    assert response.json().get("release_id") == 926397

    response = await client.post(
        "/user/me/favorites/926397",
        headers=user_token_headers,
    )
    assert response.status_code == 409
    assert response.json().get("detail") == "This release is already in your favorites"


@pytest.mark.asyncio
async def test_get_favorites(client, user_token_headers, cleanup_user_recs):
    response = await client.post(
        "/user/me/favorites/926397",
        headers=user_token_headers,
    )

    assert response.status_code == 201
    assert response.json().get("release_id") == 926397

    response = await client.get(
        "/user/me/favorites",
        headers=user_token_headers,
    )
    assert response.status_code == 200
    response_data = response.json()
    assert all(k in response_data for k in ["data", "page", "limit", "total"])
    assert response_data.get("total") == 1
    assert response_data.get("data")[0].get("release_id") == 926397
