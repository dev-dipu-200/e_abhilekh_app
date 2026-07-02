from datetime import datetime
from pydantic import BaseModel


class OrganizationBase(BaseModel):
    name: str
    address: str | None = None
    is_active: bool = True


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    is_active: bool | None = None


class OrganizationResponse(OrganizationBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
