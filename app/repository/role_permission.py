from sqlalchemy import delete, exists, select
from sqlalchemy.dialects.postgresql import insert

from app.db.models.associations import role_permissions
from app.repository.base import BaseRepository


class RolePermissionRepository(BaseRepository):
    async def grant(
        self,
        role_id: int,
        permission_id: int,
    ) -> None:
        stmt = insert(role_permissions).values(role_id=role_id, permission_id=permission_id)

        await self.session.execute(stmt)

    async def revoke(
        self,
        role_id: int,
        permission_id: int,
    ) -> None:
        stmt = delete(role_permissions).where(
            role_permissions.c.role_id == role_id,
            role_permissions.c.permission_id == permission_id,
        )

        await self.session.execute(stmt)

    async def revoke_all_from_role(self, role_id: int) -> None:
        stmt = delete(role_permissions).where(role_permissions.c.role_id == role_id)

        await self.session.execute(stmt)

    async def exists(
        self,
        role_id: int,
        permission_id: int,
    ) -> bool | None:
        stmt = select(
            exists().where(role_permissions.c.role_id == role_id, role_permissions.c.permission_id == permission_id)
        )

        result = await self.session.execute(stmt)

        return result.scalar()
