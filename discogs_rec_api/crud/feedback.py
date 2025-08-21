from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from discogs_rec_api.models import Feedback, Searches, Releases
from discogs_rec_api.exceptions import (
    SearchIdNotFound,
    FeedbackAlreadyExists,
)
from discogs_rec_api.crud.base import BaseCRUD


class FeedbackCRUD(BaseCRUD):
    """
    CRUD operations for Feedback entities.

    Provides methods for creating, reading, updating, and deleting
    user feedback from the database.
    """

    def __init__(self):
        super().__init__()
        self.model: type[Feedback] = Feedback

    async def check_feedback_exists(
        self, user_id: int, search_id: int, db: AsyncSession
    ) -> bool:
        """
        Check if feedback already exists for a user and search combination.

        Args:
            user_id: ID of the user
            search_id: ID of the search
            db: Database session

        Returns:
            bool: True if feedback exists, False otherwise
        """
        query = select(self.model.id).where(
            (self.model.user_id == user_id) & (self.model.search_id == search_id)
        )
        return await self._execute_query(query=query, db=db)

    async def write_feedback(
        self, user_id: int, search_id: int, user_feedback, db: AsyncSession
    ) -> Feedback:
        """
        Create new feedback record for a user's search.

        Args:
            user_id: ID of the user providing feedback
            search_id: ID of the search being rated
            user_feedback: Feedback data containing rankings and reports
            db: Database session

        Returns:
            Feedback: Created feedback record

        Raises:
            FeedbackAlreadyExists: If feedback already exists for this user/search combination
        """
        feedback_exists = await self.check_feedback_exists(
            user_id=user_id, search_id=search_id, db=db
        )
        if feedback_exists:
            raise FeedbackAlreadyExists(
                "You have already submited feedback for this search."
            )
        feedback = self.model(
            user_id=user_id,
            search_id=search_id,
            recommendation_rank=user_feedback.recommendation_rank,
            familiarity_rank=user_feedback.familiarity_rank,
            missing_release_reported=user_feedback.missing_release_reported,
        )
        return await self._execute_query_with_refresh(obj=feedback, db=db)

    async def get_feedback(
        self, user_id: int, page: int, limit: int, db: AsyncSession
    ) -> dict:
        """
        Retrieve paginated feedback records for a user.

        Args:
            user_id: ID of the user whose feedback to retrieve
            page: Page number for pagination
            limit: Number of records per page
            db: Database session

        Returns:
            dict: Paginated feedback data with release information
        """
        query = (
            select(
                self.model.id.label("feedback_id"),
                Releases.id.label("release_id"),
                self.model.search_id,
                self.model.recommendation_rank,
                self.model.familiarity_rank,
                self.model.missing_release_reported,
            )
            .where(self.model.user_id == user_id)
            .join(Searches, Searches.id == self.model.search_id)
            .join(Releases, Releases.id == Searches.release_id)
        )
        count_query = select(func.count(self.model.id))
        return await self._execute_paginated_query(
            query=query, count_query=count_query, page=page, limit=limit, db=db
        )

    async def get_feedback_by_search_id(
        self, user_id: int, search_id: int, db: AsyncSession
    ) -> dict:
        """
        Retrieve feedback for a specific search by a user.

        Args:
            user_id: ID of the user who provided the feedback
            search_id: ID of the search to get feedback for
            db: Database session

        Returns:
            dict: Feedback data for the specified search

        Raises:
            SearchIdNotFound: If no feedback found for the given search ID
        """
        query = (
            select(
                self.model.id.label("feedback_id"),
                self.model.recommendation_rank,
                self.model.familiarity_rank,
                self.model.missing_release_reported,
            )
            .where(
                (self.model.user_id == user_id) & (self.model.search_id == search_id)
            )
            .join(Searches, Searches.id == self.model.search_id)
            .join(Releases, Releases.id == Searches.release_id)
        )
        result = await self._execute_query(query=query, db=db, return_scalar=False)
        if not result:
            raise SearchIdNotFound(f"Could not find search id {search_id}")
        return result
