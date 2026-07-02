from datetime import datetime, date
from pydantic import BaseModel
from app.database.file_model import DocumentStatus, Priority


class DocumentBase(BaseModel):
    file_number: str | None = None
    designation: str | None = None
    subject: str
    organization_id: str
    department_id: str
    document_type_id: str
    folder_id: str | None = None
    status: DocumentStatus = DocumentStatus.NEW
    priority: Priority = Priority.MEDIUM
    amount: str | None = None
    document_date: date | None = None
    current_holder_id: str | None = None


class DocumentCreate(DocumentBase):
    parser_type: str | None = None


class DocumentUpdate(BaseModel):
    file_number: str | None = None
    designation: str | None = None
    subject: str | None = None
    department_id: str | None = None
    document_type_id: str | None = None
    folder_id: str | None = None
    status: DocumentStatus | None = None
    priority: Priority | None = None
    amount: str | None = None
    document_date: date | None = None
    current_holder_id: str | None = None
    is_starred: bool | None = None
    is_archived: bool | None = None


class DocumentResponse(DocumentBase):
    id: str
    file: str
    uploader_id: str
    is_starred: bool
    is_archived: bool
    processing_state: str
    parser_type: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FolderBase(BaseModel):
    name: str
    parent_id: str | None = None
    organization_id: str


class FolderCreate(FolderBase):
    pass


class FolderResponse(FolderBase):
    id: str
    created_by_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    query: str
    organization_id: str
    language: str = "en"
    limit: int = 10


class SearchResultItem(BaseModel):
    document_id: str
    document_subject: str | None = None
    chunk_id: str
    content: str
    score: float
    page_number: int | None = None

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    query: str
    language: str
    results: list[SearchResultItem]
