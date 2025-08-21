import pytest


@pytest.mark.asyncio
async def test_submit_feedback(client, urls, user_token_headers, cleanup_user_recs):
    rec_response = await client.post(
        "/recommend",
        json={"url": urls[0], "n_recs": 5},
        headers=user_token_headers,
    )

    assert rec_response.status_code == 200
    assert "search_id" in rec_response.json()

    feedback_response = await client.post(
        f"/user/me/feedback/{rec_response.json().get("search_id")}",
        json={"recommendation_rank": 4, "familiarity_rank": 1},
        headers=user_token_headers,
    )
    assert feedback_response.status_code == 201
    assert feedback_response.json().get("recommendation_rank") == 4
    assert feedback_response.json().get("familiarity_rank") == 1


@pytest.mark.asyncio
async def test_feedback_already_exists(
    client, urls, user_token_headers, cleanup_user_recs
):
    rec_response = await client.post(
        "/recommend",
        json={"url": urls[0], "n_recs": 5},
        headers=user_token_headers,
    )

    assert rec_response.status_code == 200
    assert "search_id" in rec_response.json()
    feedback_response = await client.post(
        f"/user/me/feedback/{rec_response.json().get("search_id")}",
        json={"recommendation_rank": 4, "familiarity_rank": 1},
        headers=user_token_headers,
    )
    assert feedback_response.status_code == 201
    feedback_response = await client.post(
        f"/user/me/feedback/{rec_response.json().get("search_id")}",
        json={"recommendation_rank": 2, "familiarity_rank": 2},
        headers=user_token_headers,
    )
    assert feedback_response.status_code == 409
    assert (
        feedback_response.json().get("detail")
        == "You have already submited feedback for this search."
    )
