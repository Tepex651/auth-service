from uuid import UUID

import structlog
from pydantic import EmailStr, SecretStr

from app.containers.auth import AuthResult, AuthTokens
from app.containers.enums import ChallengeType
from app.containers.mfa import MFAEnableRequired, MFAVerificationRequired
from app.db.models.challenge import Challenge
from app.db.models.user import User
from app.exceptions.challenge import UnsupportedChallengeType
from app.exceptions.mfa import InvalidMFACode
from app.notification.email_notification import EmailNotification
from app.service.challenge_service import ChallengeService
from app.service.mfa.service import MFAService
from app.service.token_service import TokenService
from app.service.user_service import UserService


class AuthService:
    """
    - Responsible for authentication flows
    - Creates new users during registration
    - Manages tokens
    - Handles password resets and email verification
    - Implemented MFA
    """

    def __init__(
        self,
        user_service: UserService,
        token_service: TokenService,
        challenge_service: ChallengeService,
        email_notification: EmailNotification,
        mfa_service: MFAService,
    ) -> None:
        self.user_service = user_service
        self.token_service = token_service
        self.challenge_service = challenge_service
        self.email_notification = email_notification
        self.mfa_service = mfa_service

        self.logger = structlog.get_logger(__name__)

        self._continue_fn_map = {
            ChallengeType.MFA_ENABLE: self._continue_mfa_enable,
            ChallengeType.MFA_DISABLE: self._continue_mfa_disable,
            ChallengeType.LOGIN: self._continue_login_after_mfa,
            ChallengeType.REFRESH: self._continue_refresh_after_mfa,
        }

    async def _complete_login(self, user_id: UUID) -> AuthTokens:
        user = await self.user_service.get_user(user_id)
        await self.user_service.update_last_login_now(user_id=user_id)
        tokens = await self.token_service.issue_tokens(user_id=user_id, is_admin=user.is_admin)
        self.logger.info("User logged in", user_id=user_id)

        return tokens

    async def _complete_refresh(self, user_id: UUID) -> AuthTokens:
        user = await self.user_service.get_user(user_id)
        tokens = await self.token_service.issue_tokens(user_id=user_id, is_admin=user.is_admin)
        self.logger.info("Token refreshed", user_id=user_id)

        return tokens

    async def _continue_login_after_mfa(self, challenge: Challenge) -> AuthTokens:
        tokens = await self._complete_login(user_id=challenge.user_id)
        await self.challenge_service.finish_challenge(challenge_selector=challenge.selector)

        return tokens

    async def _continue_mfa_enable(self, challenge: Challenge) -> None:
        await self.mfa_service.enable(user_id=challenge.user_id)
        await self.user_service.update_mfa_state(user_id=challenge.user_id, mfa_enabled=True)
        await self.challenge_service.finish_challenge(challenge_selector=challenge.selector)
        self.logger.info("MFA enabled", user_id=challenge.user_id, challenge_type=challenge.challenge_type)

    async def _continue_mfa_disable(self, challenge: Challenge) -> None:
        await self.mfa_service.remove(user_id=challenge.user_id)
        await self.user_service.update_mfa_state(user_id=challenge.user_id, mfa_enabled=False)
        await self.challenge_service.finish_challenge(challenge_selector=challenge.selector)
        self.logger.warning(
            "MFA disabled",
            user_id=challenge.user_id,
            challenge_type=challenge.challenge_type,
        )

    async def _continue_refresh_after_mfa(self, challenge: Challenge) -> AuthTokens:
        tokens = await self._complete_refresh(user_id=challenge.user_id)
        await self.challenge_service.finish_challenge(challenge_selector=challenge.selector)

        return tokens

    async def register(self, username: str, password: SecretStr, email: EmailStr, role_name: str) -> User:
        user = await self.user_service.create_user(
            username=username, password=password, email=email, role_name=role_name
        )
        token = await self.challenge_service.start_challenge(
            challenge_type=ChallengeType.EMAIL_VERIFICATION,
            user_id=user.id,
        )
        await self.email_notification.send_verification_email(to=email, token=token)

        return user

    async def login(self, username: str, password: SecretStr) -> AuthResult:
        user = await self.user_service.authenticate(username=username, password=password)

        if user.mfa_enabled:
            challenge_token = await self.challenge_service.start_challenge(
                challenge_type=ChallengeType.LOGIN,
                user_id=user.id,
            )
            return MFAVerificationRequired(challenge_token=challenge_token)

        return await self._complete_login(user_id=user.id)

    async def logout(self, refresh_token: str) -> None:
        token = await self.token_service.resolve_refresh_token(raw_token=refresh_token)

        await self.token_service.revoke_token(token_id=token.id)

    async def refresh_tokens(self, refresh_token: str) -> AuthResult:
        token = await self.token_service.resolve_refresh_token(raw_token=refresh_token)
        user = await self.user_service.get_user(user_id=token.user_id)

        if user.mfa_enabled:
            challenge_token = await self.challenge_service.start_challenge(
                challenge_type=ChallengeType.REFRESH,
                user_id=user.id,
            )
            return MFAVerificationRequired(challenge_token=challenge_token)

        return await self._complete_refresh(user_id=user.id)

    async def change_password(self, user_id: UUID, old_password: SecretStr, new_password: SecretStr) -> AuthTokens:
        user = await self.user_service.change_password(
            user_id=user_id,
            old_password=old_password,
            new_password=new_password,
        )
        await self.token_service.revoke_all_tokens_for_user(user_id=user.id)

        return await self.token_service.issue_tokens(user_id=user.id, is_admin=user.is_admin)

    async def initiate_password_reset(self, email: str):
        user = await self.user_service.get_user_by_email(email=email)
        challenge_token = await self.challenge_service.start_challenge(
            challenge_type=ChallengeType.PASSWORD_RESET,
            user_id=user.id,
        )

        await self.email_notification.send_refresh_password_email(
            to=email,
            token=challenge_token,
        )

    async def reset_password(self, token: str, new_password: SecretStr) -> None:
        challenge = await self.challenge_service.get_challenge(challenge_token=token)

        await self.user_service.set_password(user_id=challenge.user_id, new_password=new_password)
        await self.token_service.revoke_all_tokens_for_user(user_id=challenge.user_id)

        await self.challenge_service.finish_challenge(challenge_selector=challenge.selector)

    async def confirm_email(self, token: str) -> None:
        challenge = await self.challenge_service.get_challenge(challenge_token=token)

        await self.user_service.confirm_email(user_id=challenge.user_id, email_confirmed=True)

        await self.challenge_service.finish_challenge(challenge_selector=challenge.selector)

    async def enable_mfa(self, user: User) -> MFAEnableRequired:
        uri = await self.mfa_service.setup(user_id=user.id, email=user.email)
        token = await self.challenge_service.start_challenge(
            user_id=user.id,
            challenge_type=ChallengeType.MFA_ENABLE,
        )

        return MFAEnableRequired(
            uri=uri,
            challenge_token=token,
        )

    async def disable_mfa(self, user: User) -> MFAEnableRequired:
        uri = await self.mfa_service.get_provisioning_uri(user_id=user.id, email=user.email)
        token = await self.challenge_service.start_challenge(
            user_id=user.id,
            challenge_type=ChallengeType.MFA_DISABLE,
        )

        return MFAEnableRequired(
            uri=uri,
            challenge_token=token,
        )

    async def verify_mfa_challenge(self, code: str, challenge_token: str) -> None:
        challenge = await self.challenge_service.get_challenge(challenge_token=challenge_token)
        self.logger.info("Start verify token", challenge_type=challenge.challenge_type)

        if not await self.mfa_service.verify(user_id=challenge.user_id, code=code):
            self.logger.warning("Invalid MFA code", user_id=challenge.user_id)
            raise InvalidMFACode()

        resume_func = self._continue_fn_map.get(ChallengeType(challenge.challenge_type))

        if not resume_func:
            self.logger.error("Unsupported challenge type. Please implement logic for %s", challenge.challenge_type)
            raise UnsupportedChallengeType("Unsupported challenge type")

        await resume_func(challenge=challenge)
