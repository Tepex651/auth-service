import secrets

from app.exceptions.token import TokenFormatInvalid

from .hasher import SecureHasher


class StatefulTokenCodec:
    def __init__(self, hasher: SecureHasher):
        self.hasher = hasher

    def generate_selector(self) -> str:
        return secrets.token_urlsafe(16)

    def generate_validator(self) -> str:
        return secrets.token_urlsafe(32)

    def encode(self, selector: str, validator: str) -> str:
        return f"{selector}.{validator}"

    def split(self, raw: str) -> tuple[str, str]:
        if raw.count(".") != 1:
            raise TokenFormatInvalid("Token must contain exactly one '.' separator")

        selector, validator = raw.split(".", 1)

        return selector, validator

    def hash_validator(self, validator: str) -> str:
        return self.hasher.hash(validator)

    def verify_validator(self, validator: str, hashed: str) -> bool:
        return self.hasher.verify(validator, hashed)
