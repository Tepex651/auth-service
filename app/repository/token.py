from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert

from app.db.models.token import Token
from app.repository.base import BaseRepository


class TokenRepository(BaseRepository[Token]):
    model = Token

    async def insert(self, selector: str, validator_hash: str, user_id: UUID, expires_at: datetime) -> Token | None:
        stmt = insert(Token).values(
            selector=selector, validator_hash=validator_hash, user_id=user_id, expires_at=expires_at
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["selector"])
        stmt = stmt.returning(Token)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID) -> Token | None:
        stmt = select(Token).where(Token.user_id == user_id)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_selector(self, selector: str) -> Token | None:
        stmt = select(Token).where(Token.selector == selector)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def revoke_by_id(self, token_id: UUID) -> None:
        stmt = update(Token).where(Token.id == token_id).values(revoked=True)

        await self.session.execute(stmt)

    async def revoke_by_user_id(
        self,
        user_id: UUID,
    ) -> None:
        stmt = update(Token).where(Token.user_id == user_id).values(revoked=True)

        await self.session.execute(stmt)

    async def delet_by_user_id(
        self,
        user_id: UUID,
    ) -> None:
        stmt = delete(Token).where(Token.user_id == user_id)

        await self.session.execute(stmt)
