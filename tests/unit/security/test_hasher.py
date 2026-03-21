import pytest


def test_hash_returns_valid_bcrypt_format(hasher):
    secret = "my-secret-password"
    hashed = hasher.hash(secret)
    assert hashed.startswith("$2b$04$")
    assert len(hashed) == 60


def test_hash_generates_different_hashes_for_same_input(hasher):
    secret = "my-secret-password"

    hash_1 = hasher.hash(secret)
    hash_2 = hasher.hash(secret)

    assert hash_1 != hash_2


def test_roundtrip_correct_password(hasher):
    secret = "my-secret-password"
    hashed = hasher.hash(secret)

    assert hasher.verify(secret, hashed)


def test_verify_wrong_password_returns_false(hasher):
    secret = "my-secret-password"
    wrong_secret = "wrong-password"
    hashed = hasher.hash(secret)
    assert not hasher.verify(wrong_secret, hashed)


def test_roundtrip_empty_string(hasher):
    secret = ""
    hashed = hasher.hash(secret)
    assert hasher.verify(secret, hashed)


def test_roundtrip_special_characters(hasher):
    secret = "p@$$w0rd!#%&"
    hashed = hasher.hash(secret)
    assert hasher.verify(secret, hashed)


@pytest.mark.parametrize("invalid_input", [None, 123, 45.6, [], {}, b"bytes"])
def test_hash_raises_on_invalid_input(hasher, invalid_input):
    with pytest.raises(AttributeError):
        hasher.hash(invalid_input)


@pytest.mark.parametrize("invalid_input", [None, 123, 45.6, [], {}, b"bytes"])
def test_verify_raises_on_invalid_input(hasher, invalid_input):
    secret = "my-secret-password"
    hashed = hasher.hash(secret)

    with pytest.raises(AttributeError):
        hasher.verify(invalid_input, hashed)
