import pytest
from sqlalchemy import select
from discogs_rec_api.database import create_async_session
from discogs_rec_api.models import Recommendations, Searches


@pytest.mark.asyncio
async def test_recommend_records_no_user(client, urls):
    headers = {"Content-Type": "application/json"}
    response = await client.post(
        "/recommend",
        json={"url": urls[0], "n_recs": 5},
        headers=headers,
    )
    assert response.status_code == 200
    response_data = response.json()
    assert "recommendations" in response_data
    assert len(response_data.get("recommendations")) == 5


@pytest.mark.asyncio
async def test_recommend_records_user(
    client, user_token_headers, test_engine, test_users, urls, cleanup_user_recs
):
    test_user_id = test_users.get("testuser")
    response = await client.post(
        "/recommend",
        json={"url": urls[0], "n_recs": 5},
        headers=user_token_headers,
    )

    assert response.status_code == 200
    response_data = response.json()
    assert "recommendations" in response_data
    assert "search_id" in response_data
    assert len(response_data.get("recommendations")) == 5

    async_session = create_async_session(test_engine)
    async with async_session() as session:
        stmnt_searches = select(Searches).where(Searches.user_id == test_user_id)
        res_searches = await session.execute(stmnt_searches)
        res_searches = res_searches.scalar_one_or_none()
        assert res_searches.release_id == 335130
        assert res_searches.user_id == test_user_id

        stmnt_recs = select(Recommendations).where(
            Recommendations.search_id == res_searches.id
        )
        res_recs = await session.execute(stmnt_recs)
        res_recs = res_recs.scalars().all()
        assert len(res_recs) == 5
        assert len(set([x.search_id for x in res_recs])) == 1
        assert len(set([x.release_id for x in res_recs])) == 5


@pytest.mark.asyncio
async def test_recommend_records_batch_no_user(client, urls):
    headers = {"Content-Type": "application/json"}
    response = await client.post(
        "/recommend/batch",
        json={"urls": urls, "n_recs": 5},
        headers=headers,
    )
    response_data = response.json()
    assert response.status_code == 200
    assert len(response_data) == 2
    for rec in response_data:
        assert rec.get("input_data").get("release_id") in {335130, 926397}
        assert len(rec.get("recommendations")) == 5
        assert len(rec.get("recommendations")) == 5


@pytest.mark.asyncio
async def test_recommend_records_batch_user(
    client, user_token_headers, test_engine, test_users, urls, cleanup_user_recs
):
    test_user_id = test_users.get("testuser")
    response = await client.post(
        "/recommend/batch",
        json={"urls": urls, "n_recs": 5},
        headers=user_token_headers,
    )

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert all("input_data" in result for result in response_data)
    assert all("recommendations" in result for result in response_data)
    assert all("search_id" in result for result in response_data)
    assert all(len(result["recommendations"]) == 5 for result in response_data)

    async_session = create_async_session(test_engine)
    async with async_session() as session:
        stmnt_searches = select(Searches).where(Searches.user_id == test_user_id)
        res_searches = await session.execute(stmnt_searches)
        all_searches = res_searches.scalars().all()

        assert len(all_searches) == 2
        assert {search.release_id for search in all_searches} == {335130, 926397}
        assert all(search.user_id == test_user_id for search in all_searches)

        search_ids = [search.id for search in all_searches]
        stmnt_recs = select(Recommendations).where(
            Recommendations.search_id.in_(search_ids)
        )
        res_recs = await session.execute(stmnt_recs)
        all_recs = res_recs.scalars().all()

        assert len(all_recs) == 10

        for search_id in search_ids:
            search_recs = [rec for rec in all_recs if rec.search_id == search_id]
            assert len(search_recs) == 5
            assert len(set(rec.release_id for rec in search_recs)) == 5


@pytest.mark.asyncio
async def test_record_out_of_scope(client):
    headers = {"Content-Type": "application/json"}
    url = "https://www.discogs.com/release/1239448"
    response = await client.post(
        "/recommend",
        json={"url": url, "n_recs": 5},
        headers=headers,
    )
    assert response.status_code == 404
    assert (
        response.json().get("detail")
        == "Sorry, release id 1239448 is out of the scope of our model!"
    )


@pytest.mark.asyncio
async def test_invalid_url(client):
    headers = {"Content-Type": "application/json"}
    url = "https://www.discogs.com/mster/1239448"
    response = await client.post(
        "/recommend",
        json={"url": url, "n_recs": 5},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json().get("detail") == "Invalid URL"
