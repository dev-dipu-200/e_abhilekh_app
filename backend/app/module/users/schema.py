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
    username: str | None = None
    full_name: str | None = None
    employee_id: str | None = None
    organization_id: str | None = None
    role_id: str | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    id: str
    is_superuser: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserAISettingsResponse(BaseModel):
    ai_provider: str = "ollama"
    openai_embedding_model: str | None = None
    openai_llm_model: str | None = None
    has_openai_api_key: bool
    organization_ai_provider: str = "ollama"
    organization_openai_embedding_model: str | None = None
    organization_openai_llm_model: str | None = None
    organization_has_openai_api_key: bool


class UserAISettingsUpdate(BaseModel):
    ai_provider: str = "ollama"
    openai_api_key: str | None = None
    openai_embedding_model: str | None = None
    openai_llm_model: str | None = None
    clear_openai_api_key: bool = False
