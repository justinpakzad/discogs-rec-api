from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from discogs_rec_api.database import get_db
from discogs_rec_api.security import oauth2_scheme, optional_oauth2_scheme
from discogs_rec_api.repositories.user import UserRepository
from discogs_rec_api.repositories.search import SearchRepository
from discogs_rec_api.repositories.recommendation import RecommendationRepository
from discogs_rec_api.repositories.releases import ReleasesRepository
from discogs_rec_api.repositories.favorites import FavoritesRepository
from discogs_rec_api.repositories.feedback import FeedbackRepository
from discogs_rec_api.config import Config
from discogs_rec_api.schemas import UserResponse, UserAdminResponse

settings = Config()


async def user_repository() -> UserRepository:
    """
    Dependency for a UserRepository instance.

    Returns:
        UserRepository: Instance of UserRepository for database operations
    """
    return UserRepository()


async def favorites_repository() -> FavoritesRepository:
    """
    Dependency for a FavoritesRepository instance.

    Returns:
        FavoritesRepository: Instance of FavoritesRepository for database operations
    """
    return FavoritesRepository()


async def recommendations_repository() -> RecommendationRepository:
    """
    Dependency for a RecommendationRepository instance.

    Returns:
        RecommendationRepository: Instance of RecommendationRepository for database operations
    """
    return RecommendationRepository()


async def search_repository() -> SearchRepository:
    """
    Dependency for a SearchRepository instance.

    Returns:
        SearchRepository: Instance of SearchRepository for database operations
    """
    return SearchRepository()


async def releases_repository() -> ReleasesRepository:
    """
    Dependency for a ReleasesRepository instance.

    Returns:
        ReleasesRepository: Instance of ReleasesRepository for database operations
    """
    return ReleasesRepository()


async def feedback_repository() -> FeedbackRepository:
    """
    Dependency for a FeedbackRepository instance.

    Returns:
        FeedbackRepository: Instance of FeedbackRepository for database operations
    """
    return FeedbackRepository()


async def validate_token_and_get_user(token: str, db: AsyncSession):
    """
    Validates JWT token and returns the current authenticated user.

    Extracts and validates the JWT token from the Authorization header,
    decodes it to get the username, and retrieves the corresponding user
    from the database.

    Args:
        token: JWT token from Authorization header via oauth2_scheme
        db: Database session dependency

    Returns:
        Users: Authenticated user object

    Raises:
        HTTPException: 401 if token is invalid, expired, or user not found
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algortihm]
        )
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await UserRepository().get_user(identifier="username", value=username, db=db)
    if user is None:
        raise credentials_exception
    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: AsyncSession = Depends(get_db)
):
    """
    Dependency that validates token and returns the authenticated user.

    Validates the provided OAuth2 token and retrieves the corresponding
    user from the database. This is the base authentication dependency.

    Args:
        token: OAuth2 token from the Authorization header
        db: Database session dependency

    Returns:
        UserResponse: Authenticated user object

    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    user = await validate_token_and_get_user(token=token, db=db)
    return user


async def get_current_user_optional(
    token: Annotated[str, Depends(optional_oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
):
    """
    Dependency that optionally validates token and returns user if present.

    Similar to get_current_user but allows endpoints to work with or without
    authentication. Returns None if no token is provided.

    Args:
        token: Optional OAuth2 token from the Authorization header
        db: Database session dependency

    Returns:
        UserResponse | None: Authenticated user object or None if no token

    Raises:
        HTTPException: 400 if user account is inactive
    """
    if not token:
        return

    user = await validate_token_and_get_user(token=token, db=db)
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


async def get_current_active_user(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """
    Dependency that ensures the current user is active.

    Checks if the authenticated user has an active account status.
    Builds on get_current_user to add account status validation.

    Args:
        current_user: Authenticated user from get_current_user dependency

    Returns:
        UserResponse: Active user object

    Raises:
        HTTPException: 400 if user account is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return current_user


async def get_admin_user(
    current_user: Annotated[UserAdminResponse, Depends(get_current_user)],
):
    """
    Dependency that ensures the current user has admin privileges.

    Checks if the authenticated user has superuser/admin status.
    Used to protect admin-only endpoints.

    Args:
        current_user: Authenticated user from get_current_user dependency

    Returns:
        UserAdminResponse: Admin user object

    Raises:
        HTTPException: 403 if user does not have admin privileges
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return current_user
