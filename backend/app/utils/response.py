from typing import Any
from pydantic import BaseModel


class SuccessResponse(BaseModel):
    result: Any = None
    message: str = "Success"
    status_code: int = 200


class ErrorResponse(BaseModel):
    result: Any = None
    message: str = "Error"
    status_code: int = 400
