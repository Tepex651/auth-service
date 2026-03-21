from dataclasses import dataclass
from uuid import UUID

from app.containers.mfa import MFAVerificationRequired


@dataclass(frozen=True)
class AuthContext:
    user_id: UUID
    is_admin: bool


@dataclass
class AuthTokens:
    access_token: str
    refresh_token: str


AuthResult = AuthTokens | MFAVerificationRequired
