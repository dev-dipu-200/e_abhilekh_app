from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/e_abhilekh"
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

    class Config:
        env_file = ".env"


settings = Settings()
