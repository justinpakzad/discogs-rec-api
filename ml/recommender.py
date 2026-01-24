from cachetools import LRUCache
from ml.utils import (
    load_annoy_index,
    load_mappings,
    extract_release_id,
    validate_url,
)
from discogs_rec_api.exceptions import InvalidURL, ReleaseNotInModelError

# variables to store loaded models
mappings = None
annoy_index = None

recs_cache = LRUCache(maxsize=500)


def initialize() -> None:
    """
    Load Annoy index and mappings into memory.

    Called once during application startup to initialize
    necessary items
    """
    global annoy_index
    global mappings
    annoy_index = load_annoy_index()
    mappings = load_mappings()


def get_nearest_indices(release_id: int, n_recs: int) -> list[int]:
    """
    Get nearest neighbor indices for a release ID.

    Args:
        release_id: Discogs release ID
        n_recs: Number of recommendations requested

    Returns:
        list[int]: List of nearest neighbor indices, or None if release not found
    """
    item_index = mappings.get("release_id_to_idx").get(release_id)
    if not item_index:
        return None
    nearest_indices = annoy_index.get_nns_by_item(
        item_index, n=n_recs + 25, include_distances=False
    )
    return nearest_indices


def get_n_nearest_recs(url: str, n_recs: int = 5):
    """
    Extracts release ID from URL, finds similar releases using Annoy index,
    and returns recommendations.

    Args:
        url: Discogs release URL
        n_recs: Number of recommendations to return (default: 5)

    Returns:
        list[dict]: List of recommendations

    Raises:
        InvalidURL: If URL format is invalid
        ReleaseNotInModelError: If release is not in the recommendation model
    """
    valid_url = validate_url(url)
    if not valid_url:
        raise InvalidURL("Invalid URL")
    input_release_id = extract_release_id(url)
    cache_key = f"{input_release_id}:{n_recs}"
    if cache_key in recs_cache:
        return recs_cache[cache_key]
    indices = get_nearest_indices(release_id=input_release_id, n_recs=n_recs)
    if not indices:
        raise ReleaseNotInModelError(
            f"Sorry, release id {input_release_id} is out of the scope of our model!"
        )
    seen_artists = set()
    seen_labels = set()
    recs = []
    for idx in indices:
        release_metadata = mappings.get("idx_to_release_info").get(idx)
        artist = release_metadata.get("artist_name").strip().lower()
        label = release_metadata.get("label_name").strip().lower()
        release_id = release_metadata.get("release_id")
        url = f"https://www.discogs.com/release/{release_id}"
        if (
            artist in seen_artists
            or label in seen_labels
            or input_release_id == release_id
        ):
            continue

        recs.append(
            {
                "url": url,
                **release_metadata,
            }
        )
        seen_artists.add(artist)
        seen_labels.add(label)
        if len(recs) >= n_recs:
            break
    recs_cache[cache_key] = recs
    return recs


def get_n_nearest_recs_batch(urls: str, n_recs: int = 5) -> list[dict]:
    """
    Processes multiple Discogs release URLs and returns recommendations for each.

    Args:
        urls: List of Discogs release URLs to process
        n_recs: Number of recommendations to return per URL (default: 5)

    Returns:
        list[dict]: List of recommendations

    Raises:
        InvalidURL: If any URL format is invalid
        ReleaseNotInModelError: If any release is not in the recommendation model
    """
    result = []
    for url in urls:
        recs = {
            "input_data": {"release_id": extract_release_id(url), "url": url},
            "recommendations": get_n_nearest_recs(url=url, n_recs=n_recs),
        }
        result.append(recs)
    return result
