from fastapi import APIRouter, Query
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from discogs_rec_api.crud.releases import ReleasesCRUD

from discogs_rec_api.exceptions import (
    ReleaseNotFound,
)
from discogs_rec_api.dependencies import releases_crud, get_db

router = APIRouter(prefix="/releases", tags=["releases"])


@router.get("/styles", status_code=status.HTTP_200_OK)
async def get_styles(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=500),
    releases_crud: ReleasesCRUD = Depends(releases_crud),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get paginated list of available musical styles.

    Args:
        page: Page number for pagination (default: 1)
        limit: Number of styles per page (default: 25)
        releases_crud: Releases CRUD operations dependency
        db: Database session dependency

    Returns:
        dict: Paginated list of unique musical styles
    """
    result = await releases_crud.get_styles(page=page, limit=limit, db=db)
    return result


@router.get("/artists", status_code=status.HTTP_200_OK)
async def get_artists(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=500),
    releases_crud: ReleasesCRUD = Depends(releases_crud),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get paginated list of unique artist names.

    Args:
        page: Page number for pagination (default: 1)
        limit: Number of artists per page (default: 25)
        releases_crud: Releases CRUD operations dependency
        db: Database session dependency

    Returns:
        dict: Paginated list of artist names
    """
    result = await releases_crud.get_artists(page=page, limit=limit, db=db)
    return result


@router.get("/labels", status_code=status.HTTP_200_OK)
async def get_labels(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=500),
    releases_crud: ReleasesCRUD = Depends(releases_crud),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get paginated list of unique record label names.

    Args:
        page: Page number for pagination (default: 1)
        limit: Number of labels per page (default: 25)
        releases_crud: Releases CRUD operations dependency
        db: Database session dependency

    Returns:
        dict: Paginated list of label names
    """
    result = await releases_crud.get_labels(page=page, limit=limit, db=db)
    return result


@router.get("/countries", status_code=status.HTTP_200_OK)
async def get_countries(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=500),
    releases_crud: ReleasesCRUD = Depends(releases_crud),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get paginated list of unique countries where releases were published.

    Args:
        page: Page number for pagination (default: 1)
        limit: Number of countries per page (default: 25)
        releases_crud: Releases CRUD operations dependency
        db: Database session dependency

    Returns:
        dict: Paginated list of country names
    """
    result = await releases_crud.get_countries(page=page, limit=limit, db=db)
    return result


@router.get("/year_range", status_code=status.HTTP_200_OK)
async def get_year_range(
    releases_crud: ReleasesCRUD = Depends(releases_crud),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get the minimum and maximum release years available in the database.

    Args:
        releases_crud: Releases CRUD operations dependency
        db: Database session dependency

    Returns:
        dict: Dictionary containing min_year and max_year values
    """
    result = await releases_crud.get_year_range(db=db)
    return result


@router.get(
    "/{release_id}",
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Release not found"}},
)
async def get_release(
    release_id: int,
    db: AsyncSession = Depends(get_db),
    releases_crud: ReleasesCRUD = Depends(releases_crud),
) -> dict:
    """
    Retrieve a single release by its ID with complete metadata.

    Args:
        release_id: The unique identifier of the release
        db: Database session dependency
        releases_crud: Releases CRUD operations dependency

    Returns:
        dict: Release record with all metadata fields

    Raises:
        HTTPException: 404 if release not found
    """
    try:
        result = await releases_crud.get_release_by_id(db=db, release_id=release_id)
        return result
    except ReleaseNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("", status_code=status.HTTP_200_OK)
async def get_releases(
    artist_name: str | None = Query(
        None, description="Filter by artist name (partial match)"
    ),
    release_title: str | None = Query(
        None, description="Filter by release title (partial match)"
    ),
    country: str | None = Query(None, description="Filter by country (exact match)"),
    want_min: float | None = Query(None, description="Minimum want count", ge=0),
    want_max: float | None = Query(None, description="Maximum want count", ge=0),
    have_min: float | None = Query(None, description="Minimum have count", ge=0),
    have_max: float | None = Query(None, description="Maximum have count", ge=0),
    release_year_min: str | None = Query(None, description="Earliest release year"),
    release_year_max: str | None = Query(None, description="Latest release year"),
    styles: list[str] | None = Query(
        None, description="Filter by styles (contains any)"
    ),
    styles_exact: list[str] | None = Query(
        None, description="Filter by styles (exact)"
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=500),
    releases_crud: ReleasesCRUD = Depends(releases_crud),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Retrieve releases with filtering, pagination, and metadata.

    Supports various filter criteria including artist, title, country,
    popularity metrics, year ranges, and musical styles.

    Args:
        artist_name: Filter by artist name (partial match)
        release_title: Filter by release title (partial match)
        country: Filter by country (exact match)
        want_min: Minimum want count
        want_max: Maximum want count
        have_min: Minimum have count
        have_max: Maximum have count
        release_year_min: Earliest release year
        release_year_max: Latest release year
        styles: Filter by styles (contains any)
        styles_exact: Filter by styles (exact match)
        page: Page number for pagination (default: 1)
        limit: Number of releases per page (default: 25)
        releases_crud: Releases CRUD operations dependency
        db: Database session dependency

    Returns:
        dict: Paginated release data with metadata
    """
    filters = {k: v for k, v in locals().items() if k not in ["releases_crud", "db"]}
    result = await releases_crud.get_releases(db=db, filters=filters)
    return result
