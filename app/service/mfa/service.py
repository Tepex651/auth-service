from uuid import UUID

import structlog
from pydantic import EmailStr

from app.containers.enums import MFAMethods
from app.exceptions.mfa import MFAAlreadyEnabled, MFAEnableFailed, MFANotFound
from app.repository.mfa.user_mfa import UserMFARepository
from app.security.password.encryption import Encryption
from app.service.mfa.methods import MFAMethod


class MFAService:
    def __init__(self, mfa_method: MFAMethod, repository: UserMFARepository, encryption: Encryption) -> None:
        self.mfa_method = mfa_method
        self.repository = repository
        self.encryption = encryption

        self.logger = structlog.get_logger(__name__)

    async def setup(self, user_id: UUID, email: EmailStr) -> str:
        user_mfa = await self.repository.get_by_user_id(user_id)

        if user_mfa is None:
            secret = self.mfa_method.generate_secret()

            await self.repository.insert(
                user_id=user_id,
                secret=self.encryption.encrypt(secret),
                method=MFAMethods.TOTP,
                enabled=False,
            )

        else:
            if user_mfa.enabled:
                raise MFAAlreadyEnabled()

            secret = self.encryption.decrypt(user_mfa.secret)

        return self.mfa_method.provisioning_uri(secret, email)

    async def enable(self, user_id: UUID) -> None:
        if not await self.repository.update_enabled(user_id=user_id, enabled=True):
            raise MFAEnableFailed()

    async def remove(self, user_id: UUID) -> None:
        await self.repository.delete_by_user_id(user_id=user_id)

    async def verify(self, user_id: UUID, code: str) -> bool:
        if not (user_mfa_secret := await self.repository.get_by_user_id(user_id)):
            return False

        secret = self.encryption.decrypt(user_mfa_secret.secret)
        return self.mfa_method.verify(secret, code)

    async def get_provisioning_uri(self, user_id: UUID, email: EmailStr) -> str:
        if not (user_mfa_secret := await self.repository.get_by_user_id(user_id)):
            raise MFANotFound()

        secret = self.encryption.decrypt(user_mfa_secret.secret)
        return self.mfa_method.provisioning_uri(secret, email)
