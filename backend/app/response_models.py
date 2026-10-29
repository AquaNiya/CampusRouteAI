from typing import Any

from pydantic import BaseModel, ConfigDict


class ApiDict(BaseModel):
    model_config = ConfigDict(extra="allow")


class ErrorResponse(BaseModel):
    error: str
    detail: Any


class ApiListItem(ApiDict):
    pass
