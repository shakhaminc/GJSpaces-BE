from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseEnvelope(BaseModel, Generic[T]):
    success: bool = True
    statusCode: int = 200
    message: str = "Operation completed successfully."
    data: Optional[T] = None
    meta: Optional[dict[str, Any]] = None


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str


class ErrorEnvelope(BaseModel):
    success: bool = False
    statusCode: int
    errorCode: str
    message: str
    errors: Optional[List[ErrorDetail]] = None

