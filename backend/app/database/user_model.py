from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.base import Base
from app.utils.unique_id import generate_unique_id


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(50), primary_key=True, default=lambda: generate_unique_id(prefix="org"))
    name = Column(String(255), unique=True, nullable=False)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    ai_provider = Column(String(50), nullable=False, default="ollama")
    openai_api_key = Column(Text, nullable=True)
    openai_embedding_model = Column(String(255), nullable=True)
    openai_llm_model = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="organization")
    roles = relationship("Role", back_populates="organization")
    departments = relationship("Department", back_populates="organization")
    document_types = relationship("DocumentType", back_populates="organization")
    folders = relationship("Folder", back_populates="organization")
    documents = relationship("Document", back_populates="organization")


class Role(Base):
    __tablename__ = "roles"

    id = Column(String(50), primary_key=True, default=lambda: generate_unique_id(prefix="role"))
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    organization_id = Column(String(50), ForeignKey("organizations.id"), nullable=False)
    is_superadmin = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    is_read_only = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="roles")
    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id = Column(String(50), primary_key=True, default=lambda: generate_unique_id(prefix="user"))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(150), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    employee_id = Column(String(100), nullable=True)
    organization_id = Column(String(50), ForeignKey("organizations.id"), nullable=False)
    role_id = Column(String(50), ForeignKey("roles.id"), nullable=False)
    ai_provider = Column(String(50), nullable=False, default="ollama")
    openai_api_key = Column(Text, nullable=True)
    openai_embedding_model = Column(String(255), nullable=True)
    openai_llm_model = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="users")
    role = relationship("Role", back_populates="users")
    folders = relationship("Folder", back_populates="created_by")
    notes = relationship("Note", back_populates="author")
    documents = relationship("Document", back_populates="uploader", foreign_keys="Document.uploader_id")
