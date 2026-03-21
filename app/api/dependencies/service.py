from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.smtp_client import SMTPClient
from app.containers.enums import ChallengeType
from app.db.session import get_db_session
from app.notification.email_notification import EmailNotification
from app.repository.challenge import ChallengeRepository
from app.repository.mfa.user_mfa import UserMFARepository
from app.repository.permission import PermissionRepository
from app.repository.role import RoleRepository
from app.repository.role_permission import RolePermissionRepository
from app.repository.token import TokenRepository
from app.repository.user import UserRepository
from app.security.hasher import SecureHasher
from app.security.password.encryption import Encryption
from app.security.stateful_token import StatefulTokenCodec
from app.service.auth_service import AuthService
from app.service.challenge_service import ChallengeService
from app.service.mfa.methods import TotpMethod
from app.service.mfa.service import MFAService
from app.service.permission_service import PermissionService
from app.service.role_service import RoleService
from app.service.token_service import TokenService
from app.service.user_service import UserService
from app.settings import Settings


def get_settings_dep(request: Request):
    return request.app.state.settings


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_token_service(
    settings: SettingsDep,
    db_session: DBSessionDep,
) -> TokenService:
    return TokenService(
        secret_key=settings.token.secret_key,
        refresh_token_ttl=settings.token.refresh_ttl,
        access_token_ttl=settings.token.access_ttl,
        jwt_algorithm=settings.token.jwt_algorithm,
        token_repository=TokenRepository(db_session),
        token_codec=StatefulTokenCodec(hasher=SecureHasher(settings.app.bcrypt_cost)),
    )


def get_user_service(
    settings: SettingsDep,
    db_session: DBSessionDep,
) -> UserService:
    return UserService(
        user_repository=UserRepository(db_session),
        role_repository=RoleRepository(db_session),
        hasher=SecureHasher(settings.app.bcrypt_cost),
    )


def get_mfa_service(
    settings: SettingsDep,
    db_session: DBSessionDep,
) -> MFAService:
    return MFAService(
        mfa_method=TotpMethod(),
        repository=UserMFARepository(db_session),
        encryption=Encryption(
            current_key=settings.app.encryption_current_key,
            previous_key=settings.app.encryption_previous_key,
        ),
    )


def get_email_notification(settings: SettingsDep) -> EmailNotification:
    return EmailNotification(
        email_client=SMTPClient(
            host=settings.smtp.host,
            port=settings.smtp.port,
            username="",
            password=settings.smtp.token,
        )
    )


def get_challenge_service(settings: SettingsDep, db_session: DBSessionDep) -> ChallengeService:
    return ChallengeService(
        repository=ChallengeRepository(db_session),
        token_codec=StatefulTokenCodec(hasher=SecureHasher(settings.app.bcrypt_cost)),
        ttl_map={
            ChallengeType.PASSWORD_RESET: settings.token.reset_ttl,
            ChallengeType.LOGIN: settings.token.mfa_challenge_ttl,
            ChallengeType.MFA_ENABLE: settings.token.mfa_challenge_ttl,
            ChallengeType.MFA_DISABLE: settings.token.mfa_challenge_ttl,
            ChallengeType.EMAIL_VERIFICATION: settings.token.mfa_challenge_ttl,
        },
    )


def get_auth_service(
    user_service: Annotated[UserService, Depends(get_user_service)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    mfa_service: Annotated[MFAService, Depends(get_mfa_service)],
    challenge_service: Annotated[ChallengeService, Depends(get_challenge_service)],
    email_notification: Annotated[EmailNotification, Depends(get_email_notification)],
) -> AuthService:
    return AuthService(
        user_service=user_service,
        token_service=token_service,
        email_notification=email_notification,
        mfa_service=mfa_service,
        challenge_service=challenge_service,
    )


def get_role_service(db_session: DBSessionDep) -> RoleService:
    return RoleService(
        role_repository=RoleRepository(db_session),
        role_permission_repository=RolePermissionRepository(db_session),
        permission_service=PermissionService(
            permission_repository=PermissionRepository(db_session),
        ),
    )


def get_permission_service(db_session: DBSessionDep) -> PermissionService:
    return PermissionService(
        permission_repository=PermissionRepository(db_session),
    )
