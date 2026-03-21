from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import require_access_token
from app.api.dependencies.service import get_auth_service, get_user_service
from app.api.v1.schemas.requests.user import ChangeUserPasswordRequest
from app.api.v1.schemas.responses.token import TokenResponse
from app.api.v1.schemas.responses.user import UserResponse
from app.containers.auth import AuthContext
from app.service.auth_service import AuthService
from app.service.user_service import UserService

router = APIRouter(prefix="/v1/users/me", tags=["user"])


@router.get("", response_model=UserResponse)
async def get_me(
    user_service: Annotated[UserService, Depends(get_user_service)],
    auth_context: Annotated[AuthContext, Depends(require_access_token)],
):
    user = await user_service.get_user(auth_context.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


@router.post("/password", response_model=TokenResponse)
async def change_password(
    body: ChangeUserPasswordRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    auth_context: Annotated[AuthContext, Depends(require_access_token)],
):
    return await auth_service.change_password(
        user_id=auth_context.user_id,
        old_password=body.old_password,
        new_password=body.new_password,
    )
