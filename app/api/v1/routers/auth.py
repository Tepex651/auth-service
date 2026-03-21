from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.service import get_auth_service
from app.api.v1.schemas.queries.token import ResetPasswordQuery
from app.api.v1.schemas.requests.mfa import ConfirmMFASetupRequest
from app.api.v1.schemas.requests.token import LogoutRequest, RefreshTokenRequest
from app.api.v1.schemas.requests.user import (
    ConfirmResetUserPasswordRequest,
    CreateUserRequest,
    LoginUserRequest,
    ResetUserPasswordRequest,
)
from app.api.v1.schemas.responses.mfa import MFAEnableResponse
from app.api.v1.schemas.responses.token import LoginResponse, TokenResponse
from app.api.v1.schemas.responses.user import RegisterResponse, ResetPasswordResponse
from app.db.models.user import User
from app.service.auth_service import AuthService

router = APIRouter(prefix="/v1/auth", tags=["authentication"])
templates = Jinja2Templates(directory="app/templates")


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def register(
    body: CreateUserRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    await auth_service.register(
        username=body.username, password=body.password, email=body.email, role_name=body.role_name
    )

    return RegisterResponse(email=body.email)


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginUserRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    return await auth_service.login(username=credentials.username, password=credentials.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh(
    token: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    return await auth_service.refresh_tokens(
        refresh_token=token.refresh_token,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(
    req: LogoutRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    return await auth_service.logout(refresh_token=req.refresh_token)


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    body: ResetUserPasswordRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    await auth_service.initiate_password_reset(
        email=body.email,
    )

    return ResetPasswordResponse()


@router.get("/confirm-reset-password", response_class=HTMLResponse)
async def confirm_reset_password_page(request: Request, query: Annotated[ResetPasswordQuery, Depends()]):
    return templates.TemplateResponse(
        request=request, name="email/reset_password.html", context={"request": request, "token": query.token}
    )


@router.post("/confirm-reset-password")
async def confirm_reset_password(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    body: Annotated[ConfirmResetUserPasswordRequest, Form()],
):
    await auth_service.reset_password(
        token=body.token,
        new_password=body.new_password,
    )


@router.get("/confirm-email", status_code=status.HTTP_201_CREATED)
async def confirm_email(
    query: Annotated[ResetPasswordQuery, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    await auth_service.confirm_email(token=query.token)


@router.post("/mfa/enable", response_model=MFAEnableResponse)
async def enable_mfa(
    user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    return await auth_service.enable_mfa(user=user)


@router.post("/mfa/verify")
async def varify_mfa(
    body: ConfirmMFASetupRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    await auth_service.verify_mfa_challenge(code=body.code, challenge_token=body.challenge_token)


@router.post("/mfa/disable", response_model=MFAEnableResponse)
async def disable_mfa(
    user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    return await auth_service.disable_mfa(user)
