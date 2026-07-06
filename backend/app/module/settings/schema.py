from pydantic import BaseModel


class AISettingsResponse(BaseModel):
    ai_provider: str = "ollama"
    openai_embedding_model: str | None = None
    openai_llm_model: str | None = None
    has_openai_api_key: bool
    organization_ai_provider: str = "ollama"
    organization_openai_embedding_model: str | None = None
    organization_openai_llm_model: str | None = None
    organization_has_openai_api_key: bool


class AISettingsUpdate(BaseModel):
    ai_provider: str = "ollama"
    openai_api_key: str | None = None
    openai_embedding_model: str | None = None
    openai_llm_model: str | None = None
    clear_openai_api_key: bool = False
