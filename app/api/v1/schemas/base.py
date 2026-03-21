from typing import Literal

from pydantic import BaseModel, ConfigDict


class BaseRequestSchema(BaseModel):
    pass


class BaseResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    pass


class BaseQuerySchema(BaseModel):
    limit: int = 100
    offset: int = 0
    sort_order: Literal["asc", "desc"] = "asc"
