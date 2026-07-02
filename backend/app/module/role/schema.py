from datetime import datetime
from pydantic import BaseModel


class RoleBase(BaseModel):
    name: str
    description: str | None = None
    organization_id: str
    is_superadmin: bool = False
    is_admin: bool = False
    is_read_only: bool = False


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_superadmin: bool | None = None
    is_admin: bool | None = None
    is_read_only: bool | None = None


class RoleResponse(RoleBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
