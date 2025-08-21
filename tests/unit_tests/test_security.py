import pytest
from jose import jwt
from discogs_rec_api.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from discogs_rec_api.config import Config


@pytest.fixture
def password():
    return "mypasswordsucks303"


def test_password_hash(password):
    hashed_password = get_password_hash(password)
    assert password != hashed_password


def test_verify_password(password):
    hashed_password = get_password_hash(password)
    assert verify_password(plain_password=password, hashed_password=hashed_password)


def test_invalid_password(password):
    hashed_password = get_password_hash(password + "909")
    assert not verify_password(plain_password=password, hashed_password=hashed_password)


def test_create_access_token():
    data = {"sub": "jp303"}
    access_token = create_access_token(data=data)
    assert isinstance(access_token, str)
    assert len(access_token) > 0
    parts = access_token.split(".")
    assert len(parts) == 3


def test_decode_access_token():
    settings = Config()
    data = {"sub": "jp303"}
    access_token = create_access_token(data=data)
    decoded = jwt.decode(
        access_token, settings.secret_key, algorithms=[settings.algortihm]
    )

    assert decoded.get("sub") == "jp303"
