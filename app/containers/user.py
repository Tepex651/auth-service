from datetime import datetime

from pydantic import BaseModel, EmailStr


class CreateUserData(BaseModel):
    username: str
    hashed_password: str
    email: EmailStr


class UpdateUserData(BaseModel):
    last_login_at: datetime | None = None
    email_confirmed: bool | None = None
