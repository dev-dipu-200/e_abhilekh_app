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
    department_id: str | None = None
    document_type_id: str | None = None
    year: int | None = None
    date_from: str | None = None
    date_to: str | None = None
    status: str | None = None
    page: int = 1
    page_size: int = 10


class SearchResultItem(BaseModel):
    document_id: str
    document_subject: str | None = None
    chunk_id: str
    content: str
    score: float
    page_number: int | None = None
    match_type: str = "semantic"
    department: str | None = None
    document_type: str | None = None
    file_number: str | None = None
    file_date: str | None = None

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    query: str
    language: str
    results: list[SearchResultItem]
    total: int = 0
    page: int = 1
    has_more: bool = False
    elapsed_ms: int = 0


class DraftTemplates(BaseModel):
    id: str
    name: str
    label: str
    description: str
    icon: str = "file-text"


class DraftGenerateRequest(BaseModel):
    template_id: str
    reference_id: str
    instructions: str = ""
    language: str = "en"
    tone: str = "formal"
    fresh_generation: bool = False


class DraftGenerateResponse(BaseModel):
    draft_text: str = ""
    draft_html: str = ""
    draft_json: str = ""
    relevant_records: list[SearchResultItem] = []
    subject: str = ""
    template_id: str = ""
    language: str = "en"
    tone: str = "formal"


class DraftCheckRequest(BaseModel):
    reference_id: str
    template_id: str
    language: str = "en"


class DraftCheckResponse(BaseModel):
    exists: bool = False
    draft_id: str | None = None
    draft: DraftGenerateResponse | None = None


class DraftSaveRequest(BaseModel):
    reference_id: str
    template_id: str
    language: str = "en"
    tone: str = "formal"
    subject: str = ""
    instructions: str = ""
    draft_text: str = ""
    draft_html: str = ""
    draft_json: str = ""


class DraftExportRequest(BaseModel):
    draft_id: str
    format: str = "docx"


class DraftAttachRequest(BaseModel):
    draft_id: str
    document_id: str
