from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog

from app.containers.enums import ChallengeType
from app.db.models.challenge import Challenge
from app.exceptions.challenge import (
    ChallengeAlreadyConsumed,
    ChallengeCreationFailed,
    ChallengeExpired,
    ChallengeNotFound,
    ChallengeNotFoundOrConsumed,
    InvalidChallengeToken,
)
from app.repository.challenge import ChallengeRepository
from app.security.stateful_token import StatefulTokenCodec


class ChallengeService:
    def __init__(
        self,
        repository: ChallengeRepository,
        token_codec: StatefulTokenCodec,
        ttl_map: dict[ChallengeType, timedelta],
    ) -> None:
        self.repository = repository
        self.token_codec = token_codec
        self._ttl_map = ttl_map

        self.logger = structlog.get_logger(__name__)

    async def start_challenge(self, challenge_type: ChallengeType, user_id: UUID, payload: dict | None = None) -> str:
        selector = self.token_codec.generate_selector()
        validator = self.token_codec.generate_validator()

        expires_at = datetime.now(UTC) + self._ttl_map[challenge_type]

        if not await self.repository.insert(
            selector=selector,
            validator_hash=self.token_codec.hash_validator(validator),
            challenge_type=challenge_type,
            payload=payload,
            user_id=user_id,
            expires_at=expires_at,
        ):
            self.logger.warning("Failed to create challenge")
            raise ChallengeCreationFailed()

        self.logger.info(
            "MFA challenge created",
            challenge_type=challenge_type,
            user_id=user_id,
            selector=selector,
        )

        return f"{selector}.{validator}"

    async def finish_challenge(self, challenge_selector: str) -> None:
        if not await self.repository.update_consumed_at_now(challenge_selector=challenge_selector):
            self.logger.warning("Challenge not found or already consumed")
            raise ChallengeNotFoundOrConsumed()

    async def get_challenge(self, challenge_token: str) -> Challenge:
        selector, validator = self.token_codec.split(challenge_token)

        self.logger.debug("Searching token by selector", selector=selector)

        token = await self.repository.get_by_selector(selector=selector)

        if not token:
            self.logger.warning("Challenge not found")
            raise ChallengeNotFound()

        if token.consumed_at is not None:
            self.logger.warning("Challenge already consumed")
            raise ChallengeAlreadyConsumed()

        if token.expires_at < datetime.now(UTC):
            self.logger.warning("Challenge expired")
            raise ChallengeExpired()

        if not self.token_codec.verify_validator(validator, token.validator_hash):
            self.logger.warning("Invalid token format")
            raise InvalidChallengeToken()

        return token
