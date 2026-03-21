from collections.abc import Sequence

from app.db.models.permission import Permission
from app.repository.permission import PermissionRepository


class PermissionService:
    def __init__(self, permission_repository: PermissionRepository) -> None:
        self.permission_repository = permission_repository

    def _parse_code(self, code: str) -> tuple[str, str]:
        resource, action = code.split(":")
        return resource, action

    async def get_by_code(self, code: str) -> Permission:
        resource, action = self._parse_code(code)
        if not (permission := await self.permission_repository.get_by_resource_action(resource, action)):
            raise ValueError(f"Not found permission {code}")

        return permission

    async def list_by_codes(self, codes: set[str]) -> Sequence[Permission]:
        resource_actions = [self._parse_code(code) for code in codes]
        return await self.permission_repository.list_by_resource_action(resource_actions)

    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "asc",
    ) -> tuple[Sequence[Permission], int]:
        return await self.permission_repository.list(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )
