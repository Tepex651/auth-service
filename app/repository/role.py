from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db.models.role import Role
from app.repository.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    model = Role

    async def insert(self, name: str, description: str | None = None) -> Role | None:
        stmt = insert(Role).values(name=name, description=description)
        stmt = stmt.on_conflict_do_nothing(index_elements=["name"])
        stmt = stmt.returning(Role)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Role | None:
        stmt = select(Role).where(Role.name == name)
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_id(self, id: int) -> Role | None:
        stmt = select(Role).where(Role.id == id)
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()
