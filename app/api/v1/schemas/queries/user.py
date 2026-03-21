from pydantic import Field

from app.api.v1.schemas.base import BaseQuerySchema


class UserListQuery(BaseQuerySchema):
    sort_by: str = Field("created_at", min_length=2, max_length=50)
