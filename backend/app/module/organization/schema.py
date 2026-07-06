from datetime import datetime
from pydantic import BaseModel


class OrganizationBase(BaseModel):
    name: str
    address: str | None = None
    is_active: bool = True
    ai_provider: str = "ollama"
    openai_embedding_model: str | None = None
    openai_llm_model: str | None = None


class OrganizationCreate(OrganizationBase):
    openai_api_key: str | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    is_active: bool | None = None
    ai_provider: str | None = None
    openai_api_key: str | None = None
    openai_embedding_model: str | None = None
    openai_llm_model: str | None = None
    clear_openai_api_key: bool = False


class OrganizationResponse(OrganizationBase):
    id: str
    has_openai_api_key: bool
    created_at: datetime

    class Config:
        from_attributes = True
