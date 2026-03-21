from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

import structlog
from pydantic import SecretStr
from sqlalchemy.exc import IntegrityError

from app.constants import Roles
from app.db.models.user import User
from app.exceptions.auth import AccountDisabled, InvalidCredentials
from app.exceptions.user import (
    InvalidCurrentPassword,
    RoleNotFound,
    UserAlreadyExists,
    UserNotFound,
)
from app.logger import logger
from app.repository.role import RoleRepository
from app.repository.user import UserRepository
from app.security.hasher import SecureHasher


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        hasher: SecureHasher,
    ) -> None:
        self.hasher = hasher
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.logger = structlog.get_logger(__name__)

    async def authenticate(self, username: str, password: SecretStr) -> User:
        if not (user := await self.user_repository.get_by_username(username=username)):
            raise InvalidCredentials()

        if not self.hasher.verify(password.get_secret_value(), user.hashed_password):
            raise InvalidCredentials()

        if not user.active:
            raise AccountDisabled()

        if not user.email_confirmed:
            raise AccountDisabled()

        self.logger.info("User authenticated")

        return user

    async def create_user(self, username: str, password: SecretStr, email: str, role_name: str) -> User:
        if not (role := await self.role_repository.get_by_name(role_name)):
            self.logger.warning("Role not found", username=username, role_name=role_name)
            raise RoleNotFound()

        hashed_password = self.hasher.hash(password.get_secret_value())

        try:
            return await self.user_repository.insert(
                username=username,
                hashed_password=hashed_password,
                email=email,
                role_id=role.id,
            )
        except IntegrityError as e:
            self.logger.warning("Username already exist", username=username, role_name=role_name)
            raise UserAlreadyExists() from e

    async def get_user(self, user_id: UUID) -> User:
        if not (user := await self.user_repository.get_by_id(user_id=user_id)):
            logger.warning("User not found", user_id=user_id)
            raise UserNotFound()

        return user

    async def get_user_by_email(self, email: str) -> User:
        if not (user := await self.user_repository.get_by_email(email=email)):
            logger.warning("User not found", email=email)
            raise UserNotFound()

        return user

    async def get_users(
        self,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "asc",
    ) -> tuple[Sequence[User], int]:
        return await self.user_repository.list(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def assign_role(self, user_id: UUID, role_name: Roles) -> None:
        if not (new_role := await self.role_repository.get_by_name(name=role_name.value)):
            self.logger.warning("Role not found", user_id=user_id, role_name=role_name)
            raise RoleNotFound()

        if not await self.user_repository.update_role(user_id=user_id, role_id=new_role.id):
            logger.warning("User not found", user_id=user_id)
            raise UserNotFound()

    async def set_active(self, user_id: UUID, active: bool) -> None:
        if not await self.user_repository.update_active(user_id=user_id, active=active):
            logger.warning("User not found", user_id=user_id)
            raise UserNotFound()

    async def update_last_login_now(self, user_id: UUID) -> None:
        now = datetime.now(UTC)
        if not await self.user_repository.update_last_login(user_id=user_id, last_login_at=now):
            logger.warning("User not found", user_id=user_id)
            raise UserNotFound()

    async def update_mfa_state(self, user_id: UUID, mfa_enabled: bool) -> None:
        if not await self.user_repository.update_mfa_state(user_id=user_id, mfa_enabled=mfa_enabled):
            logger.warning("User not found", user_id=user_id)
            raise UserNotFound()

    async def set_password(self, user_id: UUID, new_password: SecretStr) -> None:
        hashed_password = self.hasher.hash(new_password.get_secret_value())

        if not await self.user_repository.update_password(user_id=user_id, hashed_password=hashed_password):
            logger.warning("User not found", user_id=user_id)
            raise UserNotFound()

    async def change_password(self, user_id: UUID, old_password: SecretStr, new_password: SecretStr) -> User:
        user = await self.get_user(user_id=user_id)

        if not self.hasher.verify(old_password.get_secret_value(), user.hashed_password):
            logger.warning("Wrong password", user_id=user_id)
            raise InvalidCurrentPassword()

        await self.set_password(user_id=user_id, new_password=new_password)

        return user

    async def confirm_email(self, user_id: UUID, email_confirmed: bool) -> None:
        if not await self.user_repository.update(user_id=user_id, email_confirmed=email_confirmed):
            logger.warning("User not found", user_id=user_id)
            raise UserNotFound()
