from pydantic import Field

from app.api.v1.schemas.base import BaseQuerySchema


class RoleListQuery(BaseQuerySchema):
    sort_by: str = Field("name", min_length=2, max_length=50)
