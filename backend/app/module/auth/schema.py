from datetime import datetime
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    username: str
    full_name: str | None = None
    is_superuser: bool
    organization_id: str


class LogoutResponse(BaseModel):
    message: str = "Logged out successfully"
