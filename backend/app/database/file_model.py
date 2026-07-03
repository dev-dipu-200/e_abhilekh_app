from datetime import datetime
import enum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Enum as SAEnum, Date
from sqlalchemy.orm import relationship
from app.database.base import Base
from app.utils.unique_id import generate_unique_id


class DocumentStatus(str, enum.Enum):
    NEW = "new"
    PENDING = "pending"
    URGENT = "urgent"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_REVIEW = "in_review"
    FORWARDED = "forwarded"


class Priority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProcessingState(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    FAILED = "FAILED"


class Department(Base):
    __tablename__ = "departments"

    id = Column(String(50), primary_key=True, default=lambda: generate_unique_id(prefix="dept"))
    name = Column(String(255), nullable=False)
    organization_id = Column(String(50), ForeignKey("organizations.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="departments")
    documents = relationship("Document", back_populates="department")


class DocumentType(Base):
    __tablename__ = "document_types"

    id = Column(String(50), primary_key=True, default=lambda: generate_unique_id(prefix="doctype"))
    name = Column(String(255), nullable=False)
    organization_id = Column(String(50), ForeignKey("organizations.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="document_types")
    documents = relationship("Document", back_populates="document_type")


class Folder(Base):
    __tablename__ = "folders"

    id = Column(String(50), primary_key=True, default=lambda: generate_unique_id(prefix="folder"))
    name = Column(String(255), nullable=False)
    parent_id = Column(String(50), ForeignKey("folders.id"), nullable=True)
    organization_id = Column(String(50), ForeignKey("organizations.id"), nullable=False)
    created_by_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    parent = relationship("Folder", remote_side="Folder.id", backref="children")
    organization = relationship("Organization", back_populates="folders")
    created_by = relationship("User", back_populates="folders")
    documents = relationship("Document", back_populates="folder")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(50), primary_key=True, default=lambda: generate_unique_id(prefix="doc"))
    file = Column(String(500), nullable=False)
    file_number = Column(String(100), nullable=True)
    designation = Column(String(255), nullable=True)
    subject = Column(Text, nullable=True)
    organization_id = Column(String(50), ForeignKey("organizations.id"), nullable=False)
    department_id = Column(String(50), ForeignKey("departments.id"), nullable=True)
    document_type_id = Column(String(50), ForeignKey("document_types.id"), nullable=True)
    folder_id = Column(String(50), ForeignKey("folders.id"), nullable=True)
    status = Column(SAEnum(DocumentStatus), default=DocumentStatus.NEW)
    priority = Column(SAEnum(Priority), default=Priority.MEDIUM)
    amount = Column(String(50), nullable=True)
    current_holder_id = Column(String(50), ForeignKey("users.id"), nullable=True)
    uploader_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    document_date = Column(Date, nullable=True)
    is_starred = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    processing_state = Column(SAEnum(ProcessingState), default=ProcessingState.PENDING)
    parser_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="documents")
    department = relationship("Department", back_populates="documents")
    document_type = relationship("DocumentType", back_populates="documents")
    folder = relationship("Folder", back_populates="documents")
    uploader = relationship("User", back_populates="documents", foreign_keys=[uploader_id])
    current_holder = relationship("User", foreign_keys=[current_holder_id])
    notes = relationship("Note", back_populates="document", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="document", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="document", cascade="all, delete-orphan")
    generated_drafts = relationship("GeneratedDraft", back_populates="document")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class Note(Base):
    __tablename__ = "notes"

    id = Column(String(50), primary_key=True, default=lambda: generate_unique_id(prefix="note"))
    content = Column(Text, nullable=False)
    document_id = Column(String(50), ForeignKey("documents.id"), nullable=False)
    author_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="notes")
    author = relationship("User", back_populates="notes")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(String(50), primary_key=True, default=lambda: generate_unique_id(prefix="attach"))
    file = Column(String(500), nullable=False)
    filename = Column(String(255), nullable=False)
    document_id = Column(String(50), ForeignKey("documents.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="attachments")


class GeneratedDraft(Base):
    __tablename__ = "generated_drafts"

    id = Column(String(50), primary_key=True, default=lambda: generate_unique_id(prefix="draft"))
    document_id = Column(String(50), ForeignKey("documents.id"), nullable=False)
    template_type = Column(String(50), nullable=False)
    language = Column(String(10), default="en")
    tone = Column(String(20), nullable=True)
    content_text = Column(Text, nullable=True)
    content_html = Column(Text, nullable=True)
    content_json = Column(Text, nullable=True)
    reference_document_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="generated_drafts")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(String(50), primary_key=True, default=lambda: generate_unique_id(prefix="log"))
    document_id = Column(String(50), ForeignKey("documents.id"), nullable=False)
    action = Column(String(100), nullable=False)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="activity_logs")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(50), primary_key=True, default=lambda: generate_unique_id(prefix="chunk"))
    document_id = Column(String(50), ForeignKey("documents.id"), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")
