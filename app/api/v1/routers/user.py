from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Security

from app.api.dependencies.auth import admin_only
from app.api.dependencies.service import get_user_service
from app.api.v1.schemas.requests.user import ActivateUserRequest, UpdateUserRoleRequest, UserListQuery
from app.api.v1.schemas.responses.user import UserListResponse, UserResponse
from app.service.user_service import UserService

router = APIRouter(prefix="/v1/users", tags=["user"], dependencies=[Security(admin_only)])


@router.get("", response_model=UserListResponse)
async def get_users(
    query: Annotated[UserListQuery, Depends()],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    return await user_service.get_users(
        limit=query.limit,
        offset=query.offset,
        sort_by=query.sort_by,
        sort_order=query.sort_order,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    return await user_service.get_user(user_id=user_id)


@router.patch("/{user_id}/role", response_model=UserResponse)
async def patch_user_role(
    user_id: UUID,
    body: UpdateUserRoleRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    return await user_service.assign_role(user_id=user_id, role_name=body.role)


@router.patch("/{user_id}/active", response_model=UserResponse)
async def patch_user_active(
    user_id: UUID, body: ActivateUserRequest, user_service: Annotated[UserService, Depends(get_user_service)]
):
    return await user_service.set_active(user_id=user_id, active=body.active)
