import pytest

from app.security.stateful_token import StatefulTokenCodec

TEST_BCRYPT_COST = 4


@pytest.fixture(scope="session")
def hasher():
    from app.security.hasher import SecureHasher

    hasher = SecureHasher(bcrypt_cost=TEST_BCRYPT_COST)
    return hasher


@pytest.fixture(scope="session")
def codec(hasher):
    return StatefulTokenCodec(hasher=hasher)
