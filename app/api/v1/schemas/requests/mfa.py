from app.api.v1.schemas.base import BaseRequestSchema


class ConfirmMFASetupRequest(BaseRequestSchema):
    challenge_token: str
    code: str
