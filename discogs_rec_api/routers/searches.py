from fastapi import APIRouter, Query
from fastapi import status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from discogs_rec_api.dependencies import (
    get_current_active_user,
    get_db,
    search_repository,
)

from discogs_rec_api.models import Users
from discogs_rec_api.repositories.search import SearchRepository


router = APIRouter(prefix="/user/me/searches", tags=["recommendations"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses={401: {"description": "Unauthorized - Authentication required"}},
)
async def get_user_searches(
    current_user: Users = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    search_repository: SearchRepository = Depends(search_repository),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=500),
) -> dict:
    """
    Get the current user's search history.

    Args:
        current_user: Current authenticated user dependency
        db: Database session dependency
        search_repository: Searche CRUD operations dependency
        page: Page number for pagination (default: 1)
        limit: Number of items per page (default: 10)

    Returns:
        list: List of releases the user has requested recommendations for

    Raises:
        HTTPException: 401 if user is not authenticated
    """

    result = await search_repository.get_user_searches(
        user_id=current_user.id, limit=limit, page=page, db=db
    )
    return result
