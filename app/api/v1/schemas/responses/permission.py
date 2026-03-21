from app.api.v1.schemas.base import BaseResponseSchema


class PermissionResponse(BaseResponseSchema):
    id: int
    code: str
    description: str


class PermissionListResponse(BaseResponseSchema):
    data: list[PermissionResponse]
    count: int
