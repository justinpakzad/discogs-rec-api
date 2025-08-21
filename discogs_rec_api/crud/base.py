from abc import ABC
from typing import Any
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseCRUD(ABC):
    """
    Base CRUD class with common pagination and query execution functionality.

    Provides reusable methods for database operations that are commonly used
    across different CRUD classes, including pagination, query execution,
    and result formatting.
    """

    def __init__(self) -> None:
        super().__init__()
        self.model: type | None = None

    def _calculate_offset(self, page: int, limit: int) -> int:
        """
        Calculate the offset for pagination based on page number and limit.

        Args:
            page: The page number (1-based)
            limit: Number of items per page

        Returns:
            int: The calculated offset for the query
        """
        return (page - 1) * limit

    def _build_paginated_query(self, query: Select, page: int, limit: int) -> Select:
        """
        Add pagination (offset and limit) to a SQLAlchemy query.

        Args:
            query: The base SQLAlchemy select query
            page: The page number (1-based)
            limit: Number of items per page

        Returns:
            Select: The query with pagination applied
        """
        return query.offset(self._calculate_offset(page, limit)).limit(limit)

    async def _execute_paginated_query(
        self,
        query: Select,
        count_query: Select,
        page: int,
        limit: int,
        db: AsyncSession,
        return_mapping: bool = True,
    ) -> dict[str, Any]:
        """
        Execute a paginated query and return formatted results with metadata.

        Args:
            query: The main SQLAlchemy select query to paginate
            count_query: Query to get the total count of records
            page: The page number (1-based)
            limit: Number of items per page
            db: Database session
            return_mapping: If True, return dict mappings; if False, return scalar values

        Returns:
            dict: Contains 'data', 'total', 'page', and 'limit' keys
        """
        result = await db.execute(self._build_paginated_query(query, page, limit))
        result_count = await db.execute(count_query)
        return {
            "data": (
                [dict(row) for row in result.mappings()]
                if return_mapping
                else result.scalars().all()
            ),
            "total": result_count.scalar_one_or_none(),
            "page": page,
            "limit": limit,
        }

    async def _execute_query(
        self, query: Select, db: AsyncSession, return_scalar: bool = True
    ) -> Any:
        """
        Execute a single query and return the result.

        Args:
            query: The SQLAlchemy select query to execute
            db: Database session
            return_scalar: If True, return scalar result; if False, return mapping

        Returns:
            Any: Query result - either scalar value, model instance, or dict mapping
        """
        result = await db.execute(query)
        if return_scalar:
            return result.scalar_one_or_none()
        else:
            row = result.mappings().one_or_none()
            return dict(row) if row else None

    async def _execute_query_with_rowcount(
        self, query: Select, db: AsyncSession
    ) -> int:
        """
        Execute a query (typically DELETE/UPDATE) and return the number of affected rows.

        Args:
            query: The SQLAlchemy query to execute (DELETE, UPDATE, INSERT)
            db: Database session

        Returns:
            int: Number of rows affected by the operation
        """
        result = await db.execute(query)
        await db.commit()
        return result.rowcount

    async def _execute_query_with_refresh(self, obj: Any, db: AsyncSession) -> Any:
        """
        Add an object to the session, commit, and refresh to get updated data.

        Args:
            obj: The SQLAlchemy model instance to add and refresh
            db: Database session

        Returns:
            Any: The refreshed model instance with updated data from database
        """
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj
