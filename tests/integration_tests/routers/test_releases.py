import pytest


@pytest.mark.asyncio
async def test_get_release_by_id(
    client,
):
    response = await client.get(
        "/releases/926397",
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data.get("id") == 926397
    assert len(response_data.keys()) == 15


@pytest.mark.asyncio
async def test_get_release(client):
    styles = ["Techno", "House"]
    response = await client.get(
        "/releases",
        params={
            "country": "Belgium",
            "styles": styles,
            "release_year_min": 1990,
            "release_year_max": 1995,
        },
    )
    assert response.status_code == 200
    response_data = response.json()
    assert all(k in response_data for k in ["data", "page", "limit", "total"])
    country = list(set([c.get("country") for c in response_data.get("data")]))
    assert len(country) == 1
    assert country[0] == "Belgium"
    for item in response_data.get("data"):
        assert any(v in styles for v in item.get("styles"))


@pytest.mark.asyncio
async def test_get_styles(client):
    styles_in_test_db = ["Ambient", "Downtempo", "House", "IDM", "Techno", "Trance"]
    response = await client.get(
        "/releases/styles",
    )
    assert response.status_code == 200
    response_data = response.json()
    assert all(k in response_data for k in ["data", "page", "limit", "total"])
    for style in response_data.get("data"):
        assert style in styles_in_test_db


@pytest.mark.asyncio
async def test_get_artists(client):
    response = await client.get(
        "/releases/artists",
    )
    assert response.status_code == 200
    response_data = response.json()
    assert all(k in response_data for k in ["data", "page", "limit", "total"])
    assert response_data.get("total") == 18


@pytest.mark.asyncio
async def test_get_labels(client):
    response = await client.get(
        "/releases/labels",
    )
    assert response.status_code == 200
    response_data = response.json()
    print(response_data)
    assert all(k in response_data for k in ["data", "page", "limit", "total"])
    assert response_data.get("total") == 18


@pytest.mark.asyncio
async def test_get_countries(client):
    response = await client.get(
        "/releases/countries",
    )
    assert response.status_code == 200
    response_data = response.json()
    assert all(k in response_data for k in ["data", "page", "limit", "total"])


@pytest.mark.asyncio
async def test_get_year_range(client):
    response = await client.get(
        "/releases/year_range",
    )
    assert response.status_code == 200
    response_data = response.json()
    assert "min_year" in response_data
    assert "max_year" in response_data
