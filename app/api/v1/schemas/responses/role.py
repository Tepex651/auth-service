from app.api.v1.schemas.base import BaseResponseSchema


class RoleResponse(BaseResponseSchema):
    id: int
    name: str
    description: str | None


class RoleListResponse(BaseResponseSchema):
    data: list[RoleResponse]
    count: int
