from typing import Literal

from pydantic import Field

from app.api.v1.schemas.base import BaseQuerySchema


class PermissionListQuery(BaseQuerySchema):
    sort_by: Literal["resource", "action"] = Field("resource", min_length=2, max_length=50)
