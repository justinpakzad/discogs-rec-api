from fastapi import APIRouter, Query
from fastapi import status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from discogs_rec_api.dependencies import (
    get_current_active_user,
    get_db,
    favorites_crud,
)
from discogs_rec_api.exceptions import ReleaseNotInFavorites, FavoriteAlreadyExists
from discogs_rec_api.models import Users
from discogs_rec_api.crud.favorites import FavoritesCRUD

router = APIRouter(prefix="/user/me/favorites", tags=["favorites"])


@router.post(
    "/{release_id}",
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Unauthorized - Authentication required"},
        409: {"description": "Conflict - Release already in favorites"},
    },
)
async def add_to_user_favorites(
    release_id: str,
    current_user: Users = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    favorites_crud: FavoritesCRUD = Depends(favorites_crud),
):
    """
    Add a release to the current user's favorites list.

    Args:
        release_id: ID of the release to add to favorites
        current_user: Current authenticated user dependency
        db: Database session dependency
        favorites_crud: Favorites CRUD operations dependency

    Returns:
        Favorites: The created favorite record

    Raises:
        HTTPException: 401 if user is not authenticated, 409 if release is already in favorites
    """
    try:
        result = await favorites_crud.add_to_favorites(
            user_id=current_user.id, release_id=release_id, db=db
        )
    except FavoriteAlreadyExists as e:
        raise HTTPException(status_code=409, detail=str(e))
    return result


@router.delete(
    "/{release_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Unauthorized - Authentication required"},
        404: {"description": "Not Found - Release not in favorites"},
    },
)
async def remove_user_favorite(
    release_id: str,
    current_user: Users = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    favorites_crud: FavoritesCRUD = Depends(favorites_crud),
):
    """
    Remove a release from the current user's favorites list.

    Args:
        release_id: ID of the release to remove from favorites
        current_user: Current authenticated user dependency
        db: Database session dependency
        favorites_crud: Favorites CRUD operations dependency

    Raises:
        HTTPException: 401 if user is not authenticated, 404 if release is not in favorites
    """
    try:
        await favorites_crud.remove_from_favorites(
            user_id=current_user.id, release_id=release_id, db=db
        )
    except ReleaseNotInFavorites as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses={401: {"description": "Unauthorized - Authentication required"}},
)
async def get_user_favorites(
    current_user: Users = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    favorites_crud: FavoritesCRUD = Depends(favorites_crud),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=500),
) -> dict:
    """
    Get the current user's favorite releases with detailed information.

    Args:
        current_user: Current authenticated user dependency
        db: Database session dependency
        favorites_crud: Favorites CRUD operations dependency
        page: Page number for pagination (default: 1)
        limit: Number of items per page (default: 25)

    Returns:
        dict: List of favorite releases with detailed metadata

    Raises:
        HTTPException: 401 if user is not authenticated
    """
    result = await favorites_crud.get_favorites(
        user_id=current_user.id, db=db, page=page, limit=limit
    )
    return result
