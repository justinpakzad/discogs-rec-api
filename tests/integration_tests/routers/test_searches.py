import pytest


@pytest.mark.asyncio
async def test_get_user_me_searches(
    client, user_token_headers, urls, cleanup_user_recs
):
    rec_response = await client.post(
        "/recommend",
        json={"url": urls[0], "n_recs": 5},
        headers=user_token_headers,
    )
    assert rec_response.status_code == 200
    user_searches_response = await client.get(
        "/user/me/searches", headers=user_token_headers
    )
    assert user_searches_response.status_code == 200
    user_searches_response_data = user_searches_response.json()
    assert all(
        k in user_searches_response_data for k in ["data", "page", "limit", "total"]
    )
    assert user_searches_response_data.get("total") == 1
    assert user_searches_response_data.get("data")[0].get("release_id") == 335130
