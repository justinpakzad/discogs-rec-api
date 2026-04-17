import uuid
from fastapi import APIRouter, Query
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from discogs_rec_api.dependencies import get_db, get_admin_user, user_repository
from discogs_rec_api.repositories.user import UserRepository
from discogs_rec_api.exceptions import UserNotFound


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/users",
    status_code=status.HTTP_200_OK,
    responses={
        403: {"description": "Forbidden - Admin access required"},
    },
)
async def get_users_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    admin_user=Depends(get_admin_user),
    user_repository=Depends(user_repository),
):
    """
    Retrieve a paginated list of all users (admin only).

    Args:
        page: Page number for pagination (default: 1)
        limit: Maximum number of users to return (default: 25)
        db: Database session dependency
        admin_user: Admin user authentication dependency
        user_repository: User CRUD operations dependency

    Returns:
        AdminListUsers: List of users and total count

    Raises:
        HTTPException: 403 if user is not an admin
    """
    users = await user_repository.list_all_users(db=db, page=page, limit=limit)
    return users


@router.get(
    "/user/{user_id}",
    status_code=status.HTTP_200_OK,
    responses={
        403: {"description": "Forbidden - Admin access required"},
        404: {"description": "User not found"},
    },
)
async def get_user_admin(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user=Depends(get_admin_user),
    user_repository: UserRepository = Depends(user_repository),
):
    """
    Retrieve detailed information about a specific user (admin only).

    Args:
        user_id: UUID of the user to retrieve
        db: Database session dependency
        admin_user: Admin user authentication dependency
        user_repository: User CRUD operations dependency

    Returns:
        UserResponse: User information

    Raises:
        HTTPException: 403 if user is not an admin, 404 if user not found
    """
    try:
        user = await user_repository.get_user(db=db, identifier="id", value=user_id)
        return user
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch(
    "/user/{user_id}/status",
    status_code=status.HTTP_200_OK,
    responses={
        403: {"description": "Forbidden - Admin access required"},
        404: {"description": "User not found"},
    },
)
async def update_user_status(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user=Depends(get_admin_user),
    user_repository: UserRepository = Depends(user_repository),
    action: str = "deactivate",
):
    """
    Update user status (activate/deactivate).

    Args:
        user_id: UUID of the user to update
        db: Database session dependency
        admin_user: Admin user authentication dependency
        user_repository: User CRUD operations dependency
        action: Action to perform ("deactivate" or "activate")

    Returns:
        UserResponse: Updated user information

    Raises:
        HTTPException: 403 if user is not an admin, 404 if user not found
    """
    try:
        user = await user_repository.update_user_status(
            db=db, user_id=user_id, action=action
        )
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    return user


@router.patch(
    "/user/{user_id}/privilege",
    status_code=status.HTTP_200_OK,
    responses={
        403: {"description": "Forbidden - Admin access required"},
        404: {"description": "User not found"},
    },
)
async def promote_to_superuser(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user=Depends(get_admin_user),
    user_repository: UserRepository = Depends(user_repository),
    action: str = "promote",
):
    """
    Update user privilege (promote/demote).

    Args:
        user_id: UUID of the user to update
        db: Database session dependency
        admin_user: Admin user authentication dependency
        user_repository: User CRUD operations dependency
        action: Action to perform ("promote" or "demote")

    Returns:
        UserResponse: Updated user information

    Raises:
        HTTPException: 403 if user is not an admin, 404 if user not found
    """

    try:
        user = await user_repository.update_user_privilege(
            db=db, user_id=user_id, action=action
        )
        return user
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/user/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"description": "Forbidden - Admin access required"},
        404: {"description": "User not found"},
    },
)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user=Depends(get_admin_user),
    user_repository: UserRepository = Depends(user_repository),
):
    """
    Delete a user permanently.

    Args:
        user_id: UUID of the user to delete
        db: Database session dependency
        admin_user: Admin user authentication dependency
        user_repository: User CRUD operations dependency

    Returns:
        None: 204 No Content on successful deletion

    Raises:
        HTTPException: 403 if user is not an admin, 404 if user not found
    """
    try:
        row_count = await user_repository.delete_user(db=db, user_id=user_id)
        return row_count
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
