from fastapi import APIRouter
from fastapi import status, Depends, HTTPException
from discogs_rec_api.dependencies import (
    get_current_active_user,
    user_repository,
    get_db,
)
from discogs_rec_api.schemas import UserResponse
from discogs_rec_api.models import Users
from discogs_rec_api.exceptions import UserNotFound

router = APIRouter(prefix="/user", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    responses={401: {"description": "Unauthorized - Authentication required"}},
)
async def read_users_me(
    current_user: Users = Depends(get_current_active_user),
) -> UserResponse:
    """
    Get information about the currently authenticated user.

    Args:
        current_user: Current authenticated user dependency

    Returns:
        UserResponse: Current user's information

    Raises:
        HTTPException: 401 if user is not authenticated
    """
    return current_user


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Unauthorized - Authentication required"},
        404: {"description": "User not found"},
    },
)
async def delete_user_me(
    current_user: Users = Depends(get_current_active_user),
    user_repository=Depends(user_repository),
    db=Depends(get_db),
):
    try:
        await user_repository.delete_user(db=db, user_id=current_user.id)
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
