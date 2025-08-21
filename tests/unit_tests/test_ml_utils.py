from ml.utils import extract_release_id, validate_url


def test_extract_release_id():
    discogs_url = "https://www.discogs.com/release/335130-FL-Untitled"
    release_id = extract_release_id(discogs_url)
    assert release_id == 335130


def test_valid_url():
    discogs_url = "https://www.discogs.com/release/335130-FL-Untitled"
    is_valid = validate_url(discogs_url)
    assert is_valid 


def test_invalid_url():
    # master releases are not valid for our model
    discogs_url = "https://www.discogs.com/master/53790-Big-L-The-Big-Picture-1974-1999"
    is_valid = validate_url(discogs_url)
    assert not is_valid 
