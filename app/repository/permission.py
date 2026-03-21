from collections.abc import Sequence

from sqlalchemy import select, tuple_
from sqlalchemy.dialects.postgresql import insert

from app.db.models.permission import Permission
from app.repository.base import BaseRepository


class PermissionRepository(BaseRepository[Permission]):
    model = Permission

    async def insert(self, resource: str, action: str, description: str | None = None) -> Permission | None:
        stmt = insert(Permission).values(resource=resource, action=action, description=description)
        stmt = stmt.on_conflict_do_nothing(index_elements=["resource", "action"])
        stmt = stmt.returning(Permission)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_resource_action(self, resource: str, action: str) -> Permission | None:
        stmt = select(Permission).where(Permission.resource == resource, Permission.action == action)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def list_by_resource_action(self, resource_actions: list[tuple[str, str]]) -> Sequence[Permission]:
        stmt = select(Permission).where(tuple_(Permission.resource, Permission.action).in_(resource_actions))

        result = await self.session.execute(stmt)

        return result.scalars().all()
