import logging
from fastapi import APIRouter
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from discogs_rec_api.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationRequestBatch,
    RecommendationResponseBatch,
)
from ml.recommender import get_n_nearest_recs, get_n_nearest_recs_batch
from ml.utils import extract_release_id
from discogs_rec_api.exceptions import InvalidURL, ReleaseNotInModelError
from discogs_rec_api.dependencies import get_current_user_optional, get_db
from discogs_rec_api.crud.recommendation import RecommendationCRUD
from discogs_rec_api.crud.search import SearchCRUD
from discogs_rec_api.models import Users

router = APIRouter(prefix="/recommend", tags=["recommender"])
logger = logging.getLogger("uvicorn")


async def write_searches_and_recommendations(
    recs: list[dict] | dict,
    request: RecommendationRequest | RecommendationRequestBatch,
    user: Users,
    db: AsyncSession,
    is_batch: bool = False,
) -> int | list[dict]:
    """
    Write search records and their associated recommendations to the database.

    Handles both single and batch recommendation operations by creating search
    records for the user's input URLs and linking the recommendations
    to those searches.

    Args:
        recs: Recommendation data (single dict or list of dicts for batch)
        request: Request object containing URL(s) and parameters
        user: Authenticated user making the request
        db: Database session
        is_batch: Whether this is a batch operation

    Returns:
        None: Data is persisted to database
    """
    recs_crud = RecommendationCRUD()
    search_crud = SearchCRUD()

    if not is_batch:
        mapping = [{extract_release_id(request.url): recs}]
    else:
        mapping = [
            {row.get("input_data").get("release_id"): row.get("recommendations")}
            for row in recs
        ]

    search_id_recs_mapping = await search_crud.write_searches(
        user_id=user.id, mapping=mapping, db=db
    )
    await recs_crud.write_recommendations(mapping=search_id_recs_mapping, db=db)
    return (
        list(search_id_recs_mapping[0].keys())[0]
        if not is_batch
        else search_id_recs_mapping
    )


def get_batch_search_id_mapping(search_ids: list[dict]) -> dict[int, int]:
    """
    Create a mapping from release_id to search_id for batch operations.

    Args:
        search_ids: List of dictionaries containing search_id to recommendations mapping

    Returns:
        dict: Mapping of release_id to search_id
    """
    search_id_mappings = {}
    for rec in search_ids:
        for key, val in rec.items():
            release_id = val[0].get("release_id")
            search_id_mappings[release_id] = key
    return search_id_mappings


def format_batch_response(recs: list[dict], search_ids: list[dict]) -> list[dict]:
    """
    Format batch recommendation response with search IDs.

    Combines recommendation data with corresponding search IDs for authenticated
    users in batch operations.

    Args:
        recs: List of recommendation dictionaries containing input_data and recommendations
        search_ids: List of dictionaries mapping search_id to recommendations

    Returns:
        list: Formatted response with search_id, input_data, and recommendations for each item
    """
    search_id_mappings = get_batch_search_id_mapping(search_ids)
    formatted_data = []
    for i, rec in enumerate(recs):
        search_id = [
            search_id_mappings.get(val.get("release_id"))
            for val in rec.get("recommendations")
            if search_id_mappings.get(val.get("release_id"))
        ]
        formatted_data.append(
            {
                "search_id": search_id[0] if search_id else None,
                "input_data": recs[i].get("input_data"),
                "recommendations": recs[i].get("recommendations"),
            }
        )
    return formatted_data


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    response_model=RecommendationResponse,
    response_model_exclude_none=True,
    responses={
        400: {"description": "Bad Request - Invalid Discogs URL"},
        404: {"description": "Not Found - Release not found in recommendation index"},
    },
)
async def recommend_records(
    request: RecommendationRequest,
    user: Users | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> list[RecommendationResponse]:
    """
    Get recommendations from Annoy Index based on a Discogs release URL.

    Args:
        request: Recommendation request containing Discogs URL and number of recommendations
        background_tasks: FastAPI background tasks for async database operations
        user: Optional authenticated user (None if anonymous)
        db: Database session dependency

    Returns:
        list: List of recommended releases with artist, title, and Discogs URL

    Raises:
        HTTPException: 400 if URL is invalid or 404 if release not found in index
    """
    try:
        recs = get_n_nearest_recs(url=request.url, n_recs=request.n_recs)

        if user:
            search_id = await write_searches_and_recommendations(
                recs=recs, request=request, user=user, db=db, is_batch=False
            )
            return {"search_id": search_id, "recommendations": recs}

        return {"recommendations": recs}
    except ReleaseNotInModelError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidURL as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/batch",
    status_code=status.HTTP_200_OK,
    response_model=list[RecommendationResponseBatch],
    response_model_exclude_none=True,
    responses={
        400: {"description": "Bad Request - Invalid Discogs URL"},
        404: {"description": "Not Found - Release not found in recommendation index"},
    },
)
async def recommend_batch_records(
    request: RecommendationRequestBatch,
    user: Users | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Get recommendations for multiple Discogs release URLs in batch.

    Args:
        request: Batch recommendation request containing multiple URLs and parameters
        background_tasks: FastAPI background tasks for async database operations
        user: Optional authenticated user (None if anonymous)
        db: Database session dependency

    Returns:
        list: List of dictionaries mapping each URL to its recommendations

    Raises:
        HTTPException: 400 if any URL is invalid or 404 if any release not found in index
    """
    try:
        recs = get_n_nearest_recs_batch(urls=request.urls, n_recs=request.n_recs)
        if user:
            search_ids = await write_searches_and_recommendations(
                recs=recs, request=request, user=user, db=db, is_batch=True
            )
            return format_batch_response(recs=recs, search_ids=search_ids)
        return recs
    except ReleaseNotInModelError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidURL as e:
        raise HTTPException(status_code=400, detail=str(e))
