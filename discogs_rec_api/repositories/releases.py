from sqlalchemy import select, func, text, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from discogs_rec_api.models import (
    Releases,
)
from discogs_rec_api.exceptions import ReleaseNotFound
from discogs_rec_api.repositories.base import BaseRepository

FILTER_MAPPINGS = {
    "artist_name": lambda query, value: query.where(
        Releases.artist_name.ilike(f"%{value}%")
    ),
    "release_title": lambda query, value: query.where(
        Releases.release_title.ilike(f"%{value}%")
    ),
    "country": lambda query, value: query.where(
        func.lower(Releases.country) == value.strip().lower()
    ),
    "want_min": lambda query, value: query.where(Releases.want >= value),
    "want_max": lambda query, value: query.where(Releases.want <= value),
    "have_min": lambda query, value: query.where(Releases.have >= value),
    "have_max": lambda query, value: query.where(Releases.have <= value),
    "release_year_min": lambda query, value: query.where(
        Releases.release_year >= int(value)
    ),
    "release_year_max": lambda query, value: query.where(
        Releases.release_year <= int(value)
    ),
    "styles": lambda query, value: query.where(Releases.styles.overlap(value)),
    "styles_exact": lambda query, value: query.where(
        text(
            "(SELECT array_agg(element ORDER BY element) FROM unnest(styles) as element) = :sorted_styles"
        )
    ).params(sorted_styles=sorted(value)),
}


class ReleasesRepository(BaseRepository):
    """
    Operations for Releases entities.

    Provides methods for reading and querying music release records
    from the database with various filtering options.
    """

    def __init__(self):
        super().__init__()
        self.model: type[Releases] = Releases

    async def get_release_by_id(self, release_id: int, db: AsyncSession) -> dict:
        """
        Retrieve a single release by its ID with complete metadata.

        Args:
            release_id: The unique identifier of the release
            db: Database session

        Returns:
            dict: Release record with all metadata fields

        Raises:
            ReleaseNotFound: If no release exists with the given ID
        """
        query = select(
            self.model.id,
            self.model.artist_name,
            self.model.styles,
            self.model.release_title,
            self.model.country,
            self.model.catno,
            self.model.label_name,
            self.model.release_year,
            self.model.want,
            self.model.have,
            self.model.want_to_have_ratio,
            self.model.video_count,
            self.model.low,
            self.model.median,
            self.model.high,
            self.model.video_urls
        ).where(self.model.id == int(release_id))
        result = await self._execute_query(query=query, db=db, return_scalar=False)

        if not result:
            raise ReleaseNotFound("Release not found in the database.")
        return result

    async def get_releases(self, filters: dict, db: AsyncSession) -> dict:
        """
        Retrieve releases with filtering, pagination, and metadata.

        Supports various filter criteria including artist, title, country,
        popularity metrics, year ranges, and musical styles.

        Args:
            filters: Query param filters (e.g., styles, artist, wants, etc)
            db: Database session

        Returns:
            dict: Paginated release data with metadata
        """
        query = select(
            self.model.id,
            self.model.artist_name,
            self.model.styles,
            self.model.release_title,
            self.model.country,
            self.model.catno,
            self.model.label_name,
            self.model.release_year,
            self.model.want,
            self.model.have,
            self.model.want_to_have_ratio,
            self.model.video_count,
            self.model.low,
            self.model.median,
            self.model.high,
            self.model.video_urls
        )
        count_query = select(func.count(self.model.id))
        page = filters.pop("page")
        limit = filters.pop("limit")

        for k, v in filters.items():
            if k in FILTER_MAPPINGS and v is not None:
                query = FILTER_MAPPINGS[k](query, v)
                count_query = FILTER_MAPPINGS[k](count_query, v)

        return await self._execute_paginated_query(
            query=query, count_query=count_query, page=page, limit=limit, db=db
        )

    async def get_styles(self, page: int, limit: int, db: AsyncSession) -> dict:
        """
        Get paginated list of available musical styles.

        Args:
            page: Page number for pagination
            limit: Number of styles per page
            db: Database session

        Returns:
            dict: Paginated list of unique styles
        """
        style_subq = select(
            distinct(func.unnest(self.model.styles)).label("style")
        ).subquery()

        query = select(style_subq.c.style).order_by(style_subq.c.style)
        count_query = select(func.count(style_subq.c.style))

        return await self._execute_paginated_query(
            query=query,
            count_query=count_query,
            page=page,
            limit=limit,
            db=db,
            return_mapping=False,
        )

    async def get_artists(self, page: int, limit: int, db: AsyncSession) -> dict:
        """
        Get paginated list of unique artist names.

        Args:
            page: Page number for pagination
            limit: Number of artists per page
            db: Database session

        Returns:
            dict: Paginated list of artist names
        """
        query = (
            select(self.model.artist_name).distinct().order_by(self.model.artist_name)
        )
        count_query = select(func.count(self.model.artist_name)).distinct()
        return await self._execute_paginated_query(
            query=query, count_query=count_query, page=page, limit=limit, db=db
        )

    async def get_labels(self, page: int, limit: int, db: AsyncSession) -> dict:
        """
        Get paginated list of unique record label names.

        Args:
            page: Page number for pagination
            limit: Number of labels per page
            db: Database session

        Returns:
            dict: Paginated list of label names
        """
        query = select(self.model.label_name).distinct().order_by(self.model.label_name)
        count_query = select(func.count(self.model.label_name)).distinct()
        return await self._execute_paginated_query(
            query=query, count_query=count_query, page=page, limit=limit, db=db
        )

    async def get_countries(self, page: int, limit: int, db: AsyncSession) -> dict:
        """
        Get paginated list of unique countries where releases were published.

        Args:
            page: Page number for pagination
            limit: Number of countries per page
            db: Database session

        Returns:
            dict: Paginated list of country names
        """
        query = select(self.model.country).distinct().order_by(self.model.country)
        count_query = select(func.count(self.model.country)).distinct()
        return await self._execute_paginated_query(
            query=query, count_query=count_query, page=page, limit=limit, db=db
        )

    async def get_year_range(self, db: AsyncSession) -> dict:
        """
        Get the minimum and maximum release years available in the database.

        Args:
            db: Database session

        Returns:
            dict: Dictionary containing min_year and max_year values
        """
        query = select(
            func.min(self.model.release_year).label("min_year"),
            func.max(self.model.release_year).label("max_year"),
        ).where(self.model.release_year.is_not(None))
        return await self._execute_query(query=query, db=db, return_scalar=False)
