import pytest


@pytest.mark.asyncio
async def test_get_user_me(client, user_token_headers):
    response = await client.get("/user/me", headers=user_token_headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data.get("username") == "testuser"
    assert response_data.get("email") == "testuser@example.com"
    assert response_data.get("is_active")


@pytest.mark.asyncio
async def test_get_user_me_not_authenticated(client):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123456790invalid",
    }
    response = await client.get("/user/me", headers=headers)
    assert response.status_code == 401
    assert response.json().get("detail") == "Could not validate credentials"


@pytest.mark.asyncio
async def test_delete_user(client):
    user = {
        "username": "justinpaktest",
        "email": "jp303@test.com",
        "password": "mypassword123",
    }
    response = await client.post(
        "/auth/register", json=user, headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 201
    login = {"username": "justinpaktest", "password": "mypassword123"}
    response = await client.post("/auth/login", data=login)
    assert response.status_code == 200
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {response.json().get("access_token")}",
    }
    response = await client.delete("/user/me", headers=headers)
    assert response.status_code == 204
