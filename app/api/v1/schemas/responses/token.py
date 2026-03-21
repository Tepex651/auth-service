from app.api.v1.schemas.base import BaseResponseSchema
from app.api.v1.schemas.responses.mfa import MFARequiredResponse


class TokenResponse(BaseResponseSchema):
    access_token: str
    token_type: str = "Bearer"  # noqa: S105

    refresh_token: str | None = None


LoginResponse = TokenResponse | MFARequiredResponse
