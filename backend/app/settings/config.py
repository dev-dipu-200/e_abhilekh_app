from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str | None = None
    DB_NAME: str = "e_abhilekh"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CORS_ORIGINS: str = "http://localhost:3000,http://frontend:3000"
    QDRANT_URL: str = "http://localhost:6333"
    GOOGLE_DOCUMENT_AI_PROJECT_ID: str = ""
    GOOGLE_DOCUMENT_AI_PROCESSOR_ID: str = ""
    GOOGLE_DOCUMENT_AI_LOCATION: str = "us"
    OLLAMA_BASE_URL: str = "https://ollamamodel.devtrust.biz"
    OLLAMA_EMBEDDING_MODEL: str = "qwen3-embedding:8b"
    OLLAMA_EMBEDDING_DIMENSIONS: int = 4096
    OLLAMA_GENERATION_MODEL: str = "qwen3:8b"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def _build_database_url(self):
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
        return self


settings = Settings()
