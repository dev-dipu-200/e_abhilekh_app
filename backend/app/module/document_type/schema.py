from datetime import datetime
from pydantic import BaseModel


class DocumentTypeBase(BaseModel):
    name: str
    organization_id: str


class DocumentTypeCreate(DocumentTypeBase):
    pass


class DocumentTypeUpdate(BaseModel):
    name: str | None = None


class DocumentTypeResponse(DocumentTypeBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
