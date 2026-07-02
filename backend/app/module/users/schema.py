from datetime import datetime
from pydantic import BaseModel


class UserBase(BaseModel):
    email: str
    username: str
    full_name: str | None = None
    employee_id: str | None = None
    organization_id: str
    role_id: str
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: str | None = None
    full_name: str | None = None
    employee_id: str | None = None
    role_id: str | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    id: str
    is_superuser: bool
    created_at: datetime

    class Config:
        from_attributes = True
