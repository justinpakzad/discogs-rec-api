from typing import Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from discogs_rec_api.models import Searches, Releases
from discogs_rec_api.repositories.base import BaseRepository


class SearchRepository(BaseRepository):
    """
    Operations for Search entities.

    Provides methods for creating and reading user searches
    from the database.
    """

    def __init__(self):
        super().__init__()
        self.model: type[Searches] = Searches

    async def get_user_searches(
        self, user_id: int, page: int, limit: int, db: AsyncSession
    ) -> dict:
        """
        Fetches releases that the user has searched for recommendations,
        including metadata about the original releases.

        Args:
            user_id: ID of the user to get searches for
            page: Page number for pagination
            limit: Number of items per page
            db: Database session

        Returns:
            list: List of search objects with release metadata
        """

        query = (
            select(
                Searches.release_id,
                Searches.created_at.label("request_at"),
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
            .join(Releases, Searches.release_id == Releases.id)
        )
        count_query = (
            select(func.count(Searches.release_id))
            .select_from(Searches)
            .where(Searches.user_id == user_id)
            .join(Releases, Searches.release_id == Releases.id)
        )
        return await self._execute_paginated_query(
            query=query, count_query=count_query, page=page, limit=limit, db=db
        )

    async def write_searches(
        self,
        user_id: int,
        mapping: list[dict],
        db: AsyncSession,
    ) -> list[dict[int, Any]]:
        """
        Create one or more search records in the database and return search ID mappings.
        Records that a user has searched for recommendations based on specific releases.
        Handles both single and batch operations.

        Args:
            user_id: ID of the user making the searches
            mapping: List of dictionaries mapping release_ids to recommendation data
                    (for single operations, pass a list with one dictionary)
            db: Database session

        Returns:
            list: List of dictionaries mapping search_id to recommendation data
        """
        search_objs = []
        for search in mapping:
            for search_release_id, recs in search.items():
                search_obj = self.model(user_id=user_id, release_id=search_release_id)
                db.add(search_obj)
                search_objs.append((search_obj, recs))
        await db.commit()
        return [{search.id: rec} for search, rec in search_objs]
