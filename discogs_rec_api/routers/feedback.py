from fastapi import APIRouter
from fastapi import status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from discogs_rec_api.dependencies import get_current_active_user, get_db, feedback_crud
from discogs_rec_api.models import Users
from discogs_rec_api.crud.feedback import FeedbackCRUD
from discogs_rec_api.schemas import FeedbackRequest, FeedbackResponse
from discogs_rec_api.exceptions import FeedbackAlreadyExists, SearchIdNotFound

router = APIRouter(prefix="/user/me/feedback", tags=["feedback"])


@router.post(
    "/{search_id}",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Unauthorized - Authentication required"},
        409: {"description": "Conflict - Feedback already exists for this search"},
    },
)
async def submit_feedback(
    request: FeedbackRequest,
    search_id: int,
    current_user: Users = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    feedback_crud: FeedbackCRUD = Depends(feedback_crud),
):
    try:
        result = await feedback_crud.write_feedback(
            user_id=current_user.id, search_id=search_id, user_feedback=request, db=db
        )
        return result
    except FeedbackAlreadyExists as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get(
    "/{search_id}",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized - Authentication required"},
        404: {"description": "Not Found - Search ID not found"},
    },
)
async def get_feedback_by_id(
    search_id: int,
    current_user: Users = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    feedback_crud: FeedbackCRUD = Depends(feedback_crud),
):
    try:
        result = await feedback_crud.get_feedback_by_search_id(
            user_id=current_user.id, search_id=search_id, db=db
        )
        return result
    except SearchIdNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses={401: {"description": "Unauthorized - Authentication required"}},
)
async def get_feedback(
    page: int = 1,
    limit: int = 25,
    current_user: Users = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    feedback_crud: FeedbackCRUD = Depends(feedback_crud),
):
    result = await feedback_crud.get_feedback(
        user_id=current_user.id, page=page, limit=limit, db=db
    )
    return result
