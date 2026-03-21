from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert

from app.db.models.user_mfa import UserMFA
from app.repository.base import BaseRepository


class UserMFARepository(BaseRepository[UserMFA]):
    model = UserMFA

    async def get_by_user_id(self, user_id: UUID) -> UserMFA | None:
        stmt = select(UserMFA).where(UserMFA.user_id == user_id)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def insert(self, user_id: UUID, secret: str, method: str, enabled: bool) -> UserMFA | None:
        stmt = insert(UserMFA).values(user_id=user_id, secret=secret, method=method, enabled=enabled)
        stmt = stmt.on_conflict_do_nothing(index_elements=["user_id"])
        stmt = stmt.returning(UserMFA)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def update_enabled(self, user_id: UUID, enabled: bool) -> bool:
        stmt = update(UserMFA).where(UserMFA.user_id == user_id).values(enabled=enabled).returning(UserMFA.id)
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none() is not None

    async def delete_by_user_id(self, user_id: UUID):
        stmt = delete(UserMFA).where(UserMFA.user_id == user_id)

        await self.session.execute(stmt)
