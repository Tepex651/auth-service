from app.api.v1.schemas.base import BaseResponseSchema


class MFAEnableResponse(BaseResponseSchema):
    uri: str
    challenge_token: str


class MFARequiredResponse(BaseResponseSchema):
    challenge_token: str
