from abc import ABC, abstractmethod

import pyotp


class MFAMethod(ABC):
    @abstractmethod
    def generate_secret(self) -> str: ...

    @abstractmethod
    def provisioning_uri(self, secret: str, user_email: str) -> str: ...

    @abstractmethod
    def verify(self, secret: str, code: str) -> bool: ...


class TotpMethod(MFAMethod):
    def generate_secret(self) -> str:
        return pyotp.random_base32()

    def provisioning_uri(self, secret: str, user_email: str) -> str:
        return pyotp.TOTP(secret).provisioning_uri(name=user_email, issuer_name="IAM")

    def verify(self, secret: str, code: str) -> bool:
        return pyotp.TOTP(secret).verify(code, valid_window=1)
