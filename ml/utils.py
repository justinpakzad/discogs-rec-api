import pickle
from pathlib import Path
from annoy import AnnoyIndex
import re


DATA_PATH = Path(__file__).parents[0] / "data"


annoy_index = None


def get_n_components() -> int:
    """
    Load number of components for annoy index
    """
    with open(DATA_PATH / "n_components.txt", "r") as f:
        n = int(f.read().strip())
    return n


def load_mappings() -> dict:
    """
    Load all pickle mapping files from the mappings directory.

    Returns:
        dict: Dictionary with mapping names as keys and loaded data as values
    """
    mappings = {}
    for item in Path(DATA_PATH).iterdir():
        if not item.name.startswith(".") and item.name.endswith(".pkl"):
            with open(item, "rb") as f:
                mappings[item.name.split(".")[0]] = pickle.load(f)
    return mappings


def load_annoy_index():
    """
    Load the Annoy index from disk.

    Returns:
        AnnoyIndex: Loaded Annoy index with 200 dimensions using angular metric
    """
    global annoy_index
    ann_file_path = str(DATA_PATH / "discogs_rec.ann")
    n_components = get_n_components()
    f = n_components
    annoy_index = AnnoyIndex(f, "angular")
    annoy_index.load(str(ann_file_path))
    return annoy_index


def extract_release_id(url: str) -> str:
    """
    Extract release ID from Discogs URL.

    Args:
        url: Discogs release URL

    Returns:
        int: Extracted release ID
    """
    release_id = int(url.split("release/")[-1].split("-")[0])
    return release_id


def validate_url(url: str) -> bool:
    """
    Validate Discogs release URL format.

    Args:
        url: URL to validate

    Returns:
        bool: True if URL matches expected Discogs format, False otherwise
    """
    pattern = r"^https://www\.discogs\.com/release/\d+(?:-[a-zA-Z0-9\-]+)?$"
    return bool(re.match(string=url, pattern=pattern))


if __name__ == "__main__":
    pass
