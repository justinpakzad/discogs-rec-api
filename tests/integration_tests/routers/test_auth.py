import pytest


@pytest.mark.asyncio
async def test_register_user(client):
    test_user = {
        "username": "justintest",
        "email": "justintest@test.com",
        "password": "ilovemylife2023030",
    }

    headers = {"Content-Type": "application/json"}

    response = await client.post("/auth/register", json=test_user, headers=headers)
    assert response.status_code == 201
    response_json = response.json()
    assert response_json.get("username") == "justintest"
    assert response_json.get("email") == "justintest@test.com"
    assert "password" not in response_json


@pytest.mark.asyncio
async def test_user_already_exists(client):
    test_user = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword123",
    }

    headers = {"Content-Type": "application/json"}
    result = await client.post("/auth/register", json=test_user, headers=headers)
    assert result.status_code == 409
    assert "User already exists" in result.json().get("detail")


@pytest.mark.asyncio
async def test_user_login(client):
    test_user = {
        "username": "testuser",
        "password": "testpassword123",
    }

    result = await client.post("/auth/login", data=test_user)
    assert result.status_code == 200
    assert "access_token" in result.json()


@pytest.mark.asyncio
async def test_user_invalid_login(client):
    test_user = {
        "username": "testuser_invalid",
        "password": "invalid",
    }

    result = await client.post("/auth/login", data=test_user)
    assert result.status_code == 401
    assert "Incorrect username or password" in result.json().get("detail")
