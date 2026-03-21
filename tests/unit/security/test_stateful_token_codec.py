import pytest

from app.exceptions.token import TokenFormatInvalid


def test_generate_selector_length(codec):
    selector = codec.generate_selector()

    assert isinstance(selector, str)
    assert 21 <= len(selector) <= 24


def test_generate_validator_length(codec):
    validator = codec.generate_validator()

    assert isinstance(validator, str)
    assert 42 <= len(validator) <= 44


def test_round_trip_encode_and_split(codec):
    selector = codec.generate_selector()
    validator = codec.generate_validator()
    token = codec.encode(selector, validator)
    # check that the token has exactly one dot
    assert token.count(".") == 1

    split_selector, split_validator = codec.split(token)

    assert split_selector == selector
    assert split_validator == validator


@pytest.mark.parametrize("invalid_token", ["", "no-dot", "too.many.dots"])
def test_split_invalid_format_raises_exception(codec, invalid_token):
    with pytest.raises(TokenFormatInvalid):
        codec.split(invalid_token)


def test_hash_validator_calls_hasher(codec, mocker):
    validator = "test-validator"
    mock_hash = mocker.patch.object(codec.hasher, "hash", return_value="hashed-validator")

    hashed = codec.hash_validator(validator)

    mock_hash.assert_called_once_with(validator)
    assert hashed == "hashed-validator"


def test_verify_validator_delegates_to_hasher(codec, mocker):
    validator = "test-validator"
    hashed = "hashed-validator"
    mock_verify = mocker.patch.object(codec.hasher, "verify", return_value=True)

    result = codec.verify_validator(validator, hashed)

    mock_verify.assert_called_once_with(validator, hashed)
    assert result is True
