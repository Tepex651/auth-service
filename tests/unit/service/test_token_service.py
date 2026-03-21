from datetime import UTC, datetime, timedelta
from uuid import uuid4
import pytest

from app.db.models.token import Token
from app.exceptions.token import TokenExpired, TokenValidatorMismatch
from app.repository.token import TokenRepository
from app.security.hasher import SecureHasher
from app.security.stateful_token import StatefulTokenCodec
from app.service.token_service import TokenService
from tests.unit.conftest import TEST_BCRYPT_COST


TEST_ACCESS_TOKEN_TTL = timedelta(minutes=15)
TEST_REFRESH_TOKEN_TTL = timedelta(hours=1)
TEST_SECRET_KEY = "TEST-SECRET-KEY"


@pytest.fixture
def token_repository(mocker):
    return mocker.AsyncMock(spec=TokenRepository)


@pytest.fixture
def token_codec():
    return StatefulTokenCodec(SecureHasher(bcrypt_cost=TEST_BCRYPT_COST))


@pytest.fixture
def token_service(token_repository, token_codec) -> TokenService:
    return TokenService(
        token_repository=token_repository,
        token_codec=token_codec,
        secret_key=TEST_SECRET_KEY,
        jwt_algorithm="HS256",
        refresh_token_ttl=TEST_REFRESH_TOKEN_TTL,
        access_token_ttl=TEST_ACCESS_TOKEN_TTL,
    )


# TEST ACCESS TOKENS
def test_issue_access_token_and_verify(token_service: TokenService):
    user_id = uuid4()
    is_admin = False
    token, ttl = token_service.issue_access_token(user_id=user_id, is_admin=is_admin)
    assert token is not None
    assert ttl == TEST_ACCESS_TOKEN_TTL.seconds

    token_data = token_service.verify_access_token(token=token)
    assert token_data["sub"] == str(user_id)
    assert token_data["is_admin"] == is_admin


def test_verify_access_token_and_verify_expired(token_service: TokenService):
    token_service.access_token_ttl = timedelta(seconds=-1)
    token, _ = token_service.issue_access_token(user_id=uuid4(), is_admin=False)

    with pytest.raises(TokenExpired):
        token_service.verify_access_token(token=token)


async def test_issue_access_token_and_verify_mismatch(token_service: TokenService):
    token, _ = token_service.issue_access_token(user_id=uuid4(), is_admin=False)

    with pytest.raises(TokenValidatorMismatch):
        token_service.verify_access_token(token=token + "invalid")


# TEST REFRESH TOKENS
async def test_issue_refresh_token_and_resolve(token_service: TokenService, token_repository, mocker):
    user_id = uuid4()
    token = Token(expires_at=datetime.now(UTC) + token_service.refresh_token_ttl, user_id=user_id)
    token_repository.get_by_selector.return_value = token
    raw_token = await token_service.issue_refresh_token(user_id=user_id)
    assert raw_token is not None
    assert "." in raw_token

    mocker.patch.object(token_service.token_codec, "verify_validator", return_value=True)
    token = await token_service.resolve_refresh_token(raw_token=raw_token)
    assert token.user_id == user_id


async def test_resolve_refresh_token_and_verify_expired(token_service: TokenService, token_repository):
    user_id = uuid4()
    token_repository.insert.return_value = True
    raw_token = await token_service.issue_refresh_token(user_id=user_id)

    token = Token(
        expires_at=datetime.now(UTC) - token_service.refresh_token_ttl,
    )
    token_repository.get_by_selector.return_value = token
    with pytest.raises(TokenExpired):
        await token_service.resolve_refresh_token(raw_token=raw_token)
