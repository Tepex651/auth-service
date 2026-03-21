from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
import structlog

from app.containers.auth import AuthTokens
from app.db.models.token import Token
from app.exceptions.token import TokenCreationFailed, TokenExpired, TokenNotFound, TokenRevoked, TokenValidatorMismatch
from app.logger import logger
from app.repository.token import TokenRepository
from app.security.stateful_token import StatefulTokenCodec


def utcnow() -> datetime:
    return datetime.now(UTC)


class TokenService:
    def __init__(
        self,
        secret_key: str,
        jwt_algorithm: str,
        refresh_token_ttl: timedelta,
        access_token_ttl: timedelta,
        token_repository: TokenRepository,
        token_codec: StatefulTokenCodec,
    ) -> None:
        self.secret_key = secret_key

        self.refresh_token_ttl = refresh_token_ttl
        self.access_token_ttl = access_token_ttl

        self.jwt_algorithm = jwt_algorithm
        self.token_repository = token_repository
        self.token_codec = token_codec

        self.logger = structlog.get_logger()

    async def _issue_stateful_token(
        self,
        *,
        user_id: UUID,
    ) -> str:
        selector = self.token_codec.generate_selector()
        validator = self.token_codec.generate_validator()
        now = utcnow()

        expires_at = now + self.refresh_token_ttl

        if not await self.token_repository.insert(
            selector=selector,
            validator_hash=self.token_codec.hash_validator(validator),
            user_id=user_id,
            expires_at=expires_at,
        ):
            self.logger.warning("Can't create token")
            raise TokenCreationFailed()

        return f"{selector}.{validator}"

    async def _resolve_stateful_token(
        self,
        *,
        raw_token: str,
    ) -> Token:
        selector, validator = self.token_codec.split(raw_token)

        extra = {"selector": selector}

        token = await self.token_repository.get_by_selector(selector=selector)

        if not token:
            self.logger.warning("Token not found", **extra)
            raise TokenNotFound()

        if token.revoked:
            self.logger.warning("Token revoked", **extra)
            raise TokenRevoked()

        if token.expires_at < utcnow():
            self.logger.warning("Token expired", **extra, expires_at=token.expires_at)
            raise TokenExpired()

        if not self.token_codec.verify_validator(validator, token.validator_hash):
            self.logger.warning("Token validation missmatch", **extra)
            raise TokenValidatorMismatch()

        logger.info("Token resolved successfully", **extra)

        return token

    # ---------- ACCESS TOKEN ----------

    def issue_access_token(
        self,
        *,
        user_id: UUID,
        is_admin: bool,
    ) -> tuple[str, int]:
        """
        Issue JWT access token and return (token, expires_in_seconds)
        """
        now = utcnow()
        expires_at = now + self.access_token_ttl

        payload = {
            "sub": str(user_id),
            "is_admin": is_admin,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "aud": "iam",
            "iss": "iam",
        }

        token = jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.jwt_algorithm,
        )

        return token, int((expires_at - now).total_seconds())

    def verify_access_token(self, token: str) -> dict[str, Any]:
        """
        Verify and decode access token.
        Raises if invalid / expired.
        """

        try:
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.jwt_algorithm],
                audience="iam",
                issuer="iam",
            )
        except jwt.ExpiredSignatureError as exc:
            self.logger.warning("Token expired", token=token)
            raise TokenExpired() from exc
        except jwt.InvalidTokenError as exc:
            self.logger.warning("Token validation missmatch", token=token)
            raise TokenValidatorMismatch() from exc

    # ---------- REFRESH TOKEN ----------

    async def issue_refresh_token(self, *, user_id: UUID) -> str:
        """
        Issue refresh token and persist it.
        Returns raw token: <selector>.<validator>
        """
        return await self._issue_stateful_token(
            user_id=user_id,
        )

    async def resolve_refresh_token(
        self,
        *,
        raw_token: str,
    ) -> Token:
        """
        Resolve raw refresh token to domain Token.
        Verifies existence, revocation, expiration, hash.
        """
        return await self._resolve_stateful_token(raw_token=raw_token)

    # ---------- PUBLIC FLOWS ----------

    async def issue_tokens(self, user_id: UUID, is_admin: bool) -> AuthTokens:
        access_token, _ = self.issue_access_token(
            user_id=user_id,
            is_admin=is_admin,
        )

        refresh_token = await self.issue_refresh_token(user_id=user_id)

        return AuthTokens(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def revoke_token(self, token_id: UUID) -> None:
        """
        Revoke a single refresh token.
        """
        await self.token_repository.revoke_by_id(token_id=token_id)

    async def revoke_all_tokens_for_user(self, user_id: UUID) -> None:
        """
        Revoke all refresh tokens for user (logout-all).
        """
        await self.token_repository.revoke_by_user_id(user_id=user_id)
