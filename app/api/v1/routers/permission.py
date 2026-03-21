from typing import Annotated

from fastapi import APIRouter, Depends, Security

from app.api.dependencies.auth import admin_only
from app.api.dependencies.service import get_permission_service
from app.api.v1.schemas.queries.permission import PermissionListQuery
from app.api.v1.schemas.responses.permission import PermissionListResponse, PermissionResponse
from app.service.permission_service import PermissionService

router = APIRouter(
    prefix="/v1/permissions",
    tags=["permission"],
    dependencies=[Security(admin_only)],
)


@router.get("", response_model=PermissionListResponse)
async def get_permissions(
    query: Annotated[PermissionListQuery, Depends()],
    permission_service: Annotated[
        PermissionService,
        Depends(get_permission_service),
    ],
) -> PermissionListResponse:
    roles, count = await permission_service.list(
        limit=query.limit,
        offset=query.offset,
        sort_by=query.sort_by,
        sort_order=query.sort_order,
    )

    roles = [PermissionResponse.model_validate(role) for role in roles]

    return PermissionListResponse(data=roles, count=count)
