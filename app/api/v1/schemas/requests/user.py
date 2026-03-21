from typing import Literal, Self

from pydantic import EmailStr, Field, SecretStr, field_validator, model_validator

from app.api.v1.schemas.base import BaseRequestSchema
from app.constants import Roles


class CreateUserRequest(BaseRequestSchema):
    username: str
    password: SecretStr
    email: EmailStr
    role_name: str
    mfa_enabled: bool = False

    @field_validator("password", mode="before")
    def validate_password(cls, password):
        if len(password) > 256:
            raise ValueError("Password too long (maximum 256 characters)")
        if "\x00" in password:
            raise ValueError("Invalid characters in password")
        if len(password) < 4:
            raise ValueError("Password too short (minimum 4 characters)")

        return password


class LoginUserRequest(BaseRequestSchema):
    username: str
    password: SecretStr


class ChangeUserPasswordRequest(BaseRequestSchema):
    old_password: SecretStr
    new_password: SecretStr


class ResetUserPasswordRequest(BaseRequestSchema):
    email: EmailStr


class ConfirmResetUserPasswordRequest(BaseRequestSchema):
    token: str
    new_password: SecretStr
    confirm_password: SecretStr

    @model_validator(mode="after")
    def validate_equal_passwords(self) -> Self:
        if self.new_password.get_secret_value() != self.confirm_password.get_secret_value():
            raise ValueError("Passwords don't match")

        return self


class UserListQuery(BaseRequestSchema):
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)
    sort_by: str = Field("created_at", min_length=2, max_length=50)
    sort_order: Literal["asc", "desc"] = Field("asc")


class UpdateUserRoleRequest(BaseRequestSchema):
    role: Roles


class ActivateUserRequest(BaseRequestSchema):
    active: bool
