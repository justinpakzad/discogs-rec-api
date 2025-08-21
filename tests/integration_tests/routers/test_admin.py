import pytest
from discogs_rec_api.database import create_async_session
from sqlalchemy import text


@pytest.mark.asyncio
async def test_get_users(client, superuser_token_headers):
    response = await client.get("/admin/users", headers=superuser_token_headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data.get("total") == 3

    for user in response_data.get("data"):
        assert user.get("username") in {"testuser", "testuser2", "superuser"}


@pytest.mark.asyncio
async def test_get_user(client, superuser_token_headers, test_users):
    test_user2_id = test_users.get("testuser2")
    response = await client.get(
        f"/admin/user/{test_user2_id}", headers=superuser_token_headers
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data.get("id") == str(test_user2_id)
    assert response_data.get("username") == "testuser2"


@pytest.mark.asyncio
async def test_update_user_status(client, superuser_token_headers, test_users):
    test_user2_id = test_users.get("testuser2")
    response = await client.patch(
        f"/admin/user/{test_user2_id}/status",
        headers=superuser_token_headers,
        params={"action": "deactivate"},
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data.get("id") == str(test_user2_id)
    assert not response_data.get("is_active")


@pytest.mark.asyncio
async def test_update_user_privilege(client, superuser_token_headers, test_users):
    test_user2_id = test_users.get("testuser2")
    response = await client.patch(
        f"/admin/user/{test_user2_id}/privilege",
        headers=superuser_token_headers,
        params={"action": "promote"},
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data.get("id") == str(test_user2_id)
    assert response_data.get("is_superuser")


@pytest.mark.asyncio
async def test_delete_user(
    client, test_engine, superuser_token_headers, deletable_user
):
    response = await client.delete(
        f"/admin/user/{deletable_user}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 204
    async_session = create_async_session(test_engine)
    async with async_session() as session:
        res = await session.execute(text("select count(*) from users"))
        assert res.scalar() == 3
