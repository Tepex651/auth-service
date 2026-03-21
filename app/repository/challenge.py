from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert

from app.db.models.challenge import Challenge
from app.repository.base import BaseRepository


class ChallengeRepository(BaseRepository[Challenge]):
    model = Challenge

    async def insert(
        self,
        selector: str,
        validator_hash: str,
        challenge_type: str,
        payload: dict | None,
        user_id: UUID,
        expires_at: datetime,
    ) -> Challenge:
        stmt = insert(Challenge).values(
            selector=selector,
            validator_hash=validator_hash,
            challenge_type=challenge_type,
            payload=payload,
            user_id=user_id,
            expires_at=expires_at,
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["selector"])
        stmt = stmt.returning(Challenge)

        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def get_by_id(self, challenge_id: UUID) -> Challenge | None:
        stmt = select(Challenge).where(Challenge.id == challenge_id)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID) -> Challenge | None:
        stmt = select(Challenge).where(Challenge.user_id == user_id)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_selector(self, selector: str) -> Challenge | None:
        stmt = select(Challenge).where(Challenge.selector == selector)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def update_consumed_at_now(self, challenge_selector: str) -> bool:
        stmt = (
            update(Challenge)
            .where(Challenge.selector == challenge_selector, Challenge.consumed_at.is_(None))
            .values(consumed_at=func.now())
        ).returning(Challenge.id)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none() is not None
