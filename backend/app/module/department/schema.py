from datetime import datetime
from pydantic import BaseModel


class DepartmentBase(BaseModel):
    name: str
    organization_id: str


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: str | None = None


class DepartmentResponse(DepartmentBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
