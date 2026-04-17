from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from discogs_rec_api.models import Favorites, Releases
from discogs_rec_api.exceptions import FavoriteAlreadyExists, ReleaseNotInFavorites
from discogs_rec_api.repositories.base import BaseRepository


class FavoritesRepository(BaseRepository):
    """
    Operations for Favorites entities.

    Provides methods for creating, reading, and deleting user favorites
    from the database.
    """

    def __init__(self):
        super().__init__()
        self.model: type[Favorites] = Favorites

    async def add_to_favorites(
        self, user_id: int, release_id: str, db: AsyncSession
    ) -> Favorites:
        """
        Add a release to user's favorites list.
        Checks for existing favorites to prevent duplicates.

        Args:
            user_id: ID of the user adding the favorite
            release_id: ID of the release to add to favorites
            db: Database session

        Returns:
            Favorites: The created favorite record

        Raises:
            FavoriteAlreadyExists: If the release is already in user's favorites
        """
        check_favorite = await db.execute(
            select(self.model).where(
                (self.model.user_id == user_id)
                & (self.model.release_id == int(release_id))
            )
        )
        favorite_exists = check_favorite.scalar_one_or_none()
        if favorite_exists:
            raise FavoriteAlreadyExists("This release is already in your favorites")

        favorite = self.model(user_id=user_id, release_id=int(release_id))
        return await self._execute_query_with_refresh(obj=favorite, db=db)

    async def remove_from_favorites(
        self, user_id: int, release_id: str, db: AsyncSession
    ) -> int:
        """
        Remove a release from user's favorites list.

        Args:
            user_id: ID of the user removing the favorite
            release_id: ID of the release to remove from favorites
            db: Database session

        Returns:
            int: Number of rows affected (should be 1 if successful)

        Raises:
            ReleaseNotInFavorites: If the release is not in user's favorites
        """
        query = delete(self.model).where(
            (self.model.user_id == user_id) & (self.model.release_id == int(release_id))
        )

        rowcount = await self._execute_query_with_rowcount(query=query, db=db)
        if rowcount == 0:
            raise ReleaseNotInFavorites("Release not found in favorites")

    async def get_favorites(
        self, user_id: int, page: int, limit: int, db: AsyncSession
    ) -> list[dict]:
        """
        Fetches user's favorite releases with detailed release information.
        Includes metadata about each favorited release.

        Args:
            user_id: ID of the user to get favorites for
            page: Page number for pagination
            limit: Number of items per page
            db: Database session

        Returns:
            list: List of favorite releases with detailed metadata
        """

        query = (
            select(
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
            .select_from(self.model)
            .where(self.model.user_id == user_id)
            .join(Releases, Releases.id == self.model.release_id)
        )
        count_query = (
            select(func.count(Releases.id))
            .select_from(self.model)
            .where(self.model.user_id == user_id)
            .join(Releases, Releases.id == self.model.release_id)
        )
        return await self._execute_paginated_query(
            query=query, count_query=count_query, page=page, limit=limit, db=db
        )
