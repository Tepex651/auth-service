from datetime import datetime
from uuid import UUID

from pydantic import EmailStr

from app.api.v1.schemas.base import BaseResponseSchema


class UserResponse(BaseResponseSchema):
    id: UUID
    username: str
    email: EmailStr

    created_at: datetime
    last_login_at: datetime | None


class UserListResponse(BaseResponseSchema):
    data: list[UserResponse]
    count: int


class RegisterResponse(BaseResponseSchema):
    message: str = "Check your email to verify"
    email: EmailStr


class ResetPasswordResponse(BaseResponseSchema):
    message: str = "Initiated password reset. Please check your email for further instructions."
