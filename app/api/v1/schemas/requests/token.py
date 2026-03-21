from app.api.v1.schemas.base import BaseRequestSchema


class RefreshTokenRequest(BaseRequestSchema):
    refresh_token: str


class LogoutRequest(BaseRequestSchema):
    refresh_token: str
