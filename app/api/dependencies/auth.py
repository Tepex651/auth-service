from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import OAuth2PasswordBearer

from app.api.dependencies.service import get_token_service, get_user_service
from app.containers.auth import AuthContext
from app.db.models.user import User
from app.service.token_service import TokenService
from app.service.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", refreshUrl="/api/v1/auth/refresh")


def require_access_token(
    request: Request,
    token_service: Annotated[TokenService, Depends(get_token_service)],
    token: str = Security(oauth2_scheme),
) -> AuthContext:
    try:
        decoded = token_service.verify_access_token(token=token)
        auth_context = AuthContext(
            user_id=UUID(decoded.get("sub")),
            is_admin=decoded.get("is_admin", False),
        )

        request.state.auth_context = auth_context

        return auth_context

    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        ) from err


def admin_only():
    def dependency(auth_context: Annotated[AuthContext, Depends(require_access_token)]):
        if not auth_context.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )

    return dependency


async def get_current_user(
    auth_context: Annotated[AuthContext, Depends(require_access_token)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User:
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

    if not user.email_confirmed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first.",
        )

    return user
