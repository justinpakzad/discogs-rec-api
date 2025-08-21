import pytest


@pytest.mark.asyncio
async def test_get_user_me_recs(client, user_token_headers, urls, cleanup_user_recs):
    rec_response = await client.post(
        "/recommend",
        json={"url": urls[0], "n_recs": 5},
        headers=user_token_headers,
    )
    assert rec_response.status_code == 200
    user_recs_response = await client.get(
        "/user/me/recommendations", headers=user_token_headers
    )
    assert user_recs_response.status_code == 200
    user_recs_response_data = user_recs_response.json()
    assert all(k in user_recs_response_data for k in ["data", "page", "limit", "total"])
    assert user_recs_response_data.get("total") == 5
