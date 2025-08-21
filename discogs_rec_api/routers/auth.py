from typing import Annotated
from fastapi import APIRouter
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from discogs_rec_api.dependencies import (
    get_db,
    user_crud,
)
from discogs_rec_api.schemas import (
    UserCreate,
    UserResponse,
)
from discogs_rec_api.security import create_access_token
from discogs_rec_api.schemas import Token

from discogs_rec_api.exceptions import UserAlreadyExists, UserNotFound

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": "Conflict - User already exists"},
    },
)
async def register_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    user_crud=Depends(user_crud),
):
    """
    Register a new user in the system.

    Args:
        user: User registration data (username, email, password)
        db: Database session dependency
        user_crud: User CRUD operations dependency

    Returns:
        UserResponse: Created user data (without password)

    Raises:
        HTTPException: 409 If user creation fails (e.g., duplicate username/email)
    """

    try:
        user = await user_crud.create_user(db=db, user=user)
        return user
    except UserAlreadyExists as e:
        raise HTTPException(status_code=409, detail=(str(e)))


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized - Incorrect username or password"},
    },
)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
    user_crud=Depends(user_crud),
):
    """
    Authenticate user and return JWT access token.

    Args:
        form_data: OAuth2 form containing username and password
        db: Database session dependency
        user_crud: User CRUD operations dependency

    Returns:
        Token: JWT access token and token type

    Raises:
        HTTPException: 401 if authentication fails
    """
    try:
        user = await user_crud.authenticate_user(
            db=db, username=form_data.username, password=form_data.password
        )
        access_token = create_access_token(data={"sub": user.username})
        return Token(access_token=access_token, token_type="bearer")
    except UserNotFound:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
        )
