from collections.abc import Sequence

from app.db.models.role import Role
from app.repository.role import RoleRepository
from app.repository.role_permission import RolePermissionRepository
from app.service.permission_service import PermissionService


class RoleService:
    def __init__(
        self,
        role_repository: RoleRepository,
        role_permission_repository: RolePermissionRepository,
        permission_service: PermissionService,
    ) -> None:
        self.role_repository = role_repository
        self.role_permission_repository = role_permission_repository
        self.permission_service = permission_service

    async def create(self, name: str, description: str | None = None) -> Role:
        if not (new_role := await self.role_repository.insert(name=name, description=description)):
            raise ValueError("Role creation failed!")

        return new_role

    async def update_role_permissions(self, role_id: int, permission_codes: set[str]) -> Role:
        if not (role := await self.role_repository.get_by_id(role_id)):
            raise ValueError(f"Role {role_id} not exist!")

        if not (permissions := await self.permission_service.list_by_codes(permission_codes)):
            raise ValueError("Permissions not exist. You have to create it first.")

        await self.role_permission_repository.revoke_all_from_role(role.id)
        for permission in permissions:
            await self.role_permission_repository.grant(role_id=role.id, permission_id=permission.id)

        return role

    async def get_roles(self, limit: int, offset: int, sort_by: str, sort_order: str) -> tuple[Sequence[Role], int]:
        return await self.role_repository.list(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )
