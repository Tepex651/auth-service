from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert

from app.db.models.user import User
from app.repository.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def insert(self, username: str, hashed_password: str, email: str, role_id: int, active: bool = True) -> User:
        stmt = insert(User).values(
            username=username, hashed_password=hashed_password, email=email, role_id=role_id, active=active
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["email"])
        stmt = stmt.returning(User)

        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def update(self, user_id: UUID, **values) -> bool:
        stmt = update(User).where(User.id == user_id).values(**values).returning(User.id)
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none() is not None

    async def update_last_login(self, user_id: UUID, last_login_at: datetime) -> bool:
        stmt = update(User).where(User.id == user_id).values(last_login_at=last_login_at).returning(User.id)
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none() is not None

    async def update_mfa_state(self, user_id: UUID, mfa_enabled: bool) -> bool:
        stmt = update(User).where(User.id == user_id).values(mfa_enabled=mfa_enabled).returning(User.id)
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none() is not None

    async def update_role(self, user_id: UUID, role_id: int) -> bool:
        stmt = update(User).where(User.id == user_id).values(role_id=role_id).returning(User.id)
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none() is not None

    async def update_active(self, user_id: UUID, active: bool) -> bool:
        stmt = update(User).where(User.id == user_id).values(active=active).returning(User.id)
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none() is not None

    async def update_password(self, user_id: UUID, hashed_password: str) -> bool:
        stmt = update(User).where(User.id == user_id).values(hashed_password=hashed_password).returning(User.id)
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none() is not None

    async def update_email_confirm(self, user_id: UUID, email_confirmed: bool) -> bool:
        stmt = update(User).where(User.id == user_id).values(email_confirmed=email_confirmed).returning(User.id)
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none() is not None

    async def delete_by_id(self, user_id: UUID) -> None:
        stmt = delete(User).where(User.id == user_id)

        await self.session.execute(stmt)
