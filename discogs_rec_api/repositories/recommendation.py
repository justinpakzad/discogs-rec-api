from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from discogs_rec_api.models import Recommendations, Searches, Releases
from discogs_rec_api.repositories.base import BaseRepository


class RecommendationRepository(BaseRepository):
    """
    Pperations for Recommendation entities.

    Provides methods for creating and reading user recommendations
    from the database.
    """

    def __init__(self):
        super().__init__()
        self.model: type[Recommendations] = Recommendations

    async def get_user_recommendations(
        self, user_id: int, page: int, limit: int, db: AsyncSession
    ) -> dict:
        """
        Fetches recommendations from the user's search history.
        Includes metadata about the recommended releases.

        Args:
            user_id: ID of the user to get recommendations for
            page: Page number for pagination
            limit: Number of items per page
            db: Database session

        Returns:
            list: List of recommendation objects with release metadata and source URL
        """
        query = (
            select(
                Searches.release_id.label("request_release_id"),
                Searches.created_at.label("recommended_at"),
                Releases.id.label("release_id"),
                Releases.release_title,
                Releases.artist_name,
                Releases.label_name,
                Releases.release_year,
                Releases.country,
                Releases.styles,
                Releases.want,
                Releases.have,
            )
            .select_from(Searches)
            .where(Searches.user_id == user_id)
            .join(Recommendations, Searches.id == Recommendations.search_id)
            .join(Releases, Recommendations.release_id == Releases.id)
        )
        count_query = (
            select(func.count(Searches.release_id))
            .select_from(Searches)
            .where(Searches.user_id == user_id)
            .join(Recommendations, Searches.id == Recommendations.search_id)
            .join(Releases, Recommendations.release_id == Releases.id)
        )
        response = await self._execute_paginated_query(
            query=query, count_query=count_query, page=page, limit=limit, db=db
        )
        response["data"] = [
            {
                **{k: v for k, v in row.items() if k != "request_release_id"},
                "recommended_from": f"https://www.discogs.com/release/{row['request_release_id']}",
            }
            for row in response.get("data")
        ]
        return response

    async def write_recommendations(
        self, mapping: list[dict], db: AsyncSession
    ) -> None:
        """
        Create one or more recommendation records in the database.
        Stores recommendations generated from searches and links each
        recommendation to the originating search. Handles both single
        and batch operations.

        Args:
            mapping: List of dictionaries mapping search_id to recommendation data
                    (for single operations, pass a list with one dictionary)
            db: Database session

        Returns:
            None: Commits the recommendations to database
        """
        for searches in mapping:
            for search_id, rec in searches.items():
                for value in rec:
                    recs = self.model(
                        search_id=search_id, release_id=value.get("release_id")
                    )
                    db.add(recs)
        await db.commit()
