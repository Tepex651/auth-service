from pydantic import field_validator

from app.api.v1.schemas.base import BaseRequestSchema


class CreateRoleRequest(BaseRequestSchema):
    name: str
    description: str | None = None


class AdminUpdateRolePermissionsRequest(BaseRequestSchema):
    permissions: set[str]

    @field_validator("permissions")
    def validate_codes(cls, values):
        for code in values:
            if ":" not in code:
                raise ValueError("Invalid permission code")
        return values
