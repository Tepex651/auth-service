from app.api.v1.schemas.base import BaseQuerySchema


class ResetPasswordQuery(BaseQuerySchema):
    token: str
