import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import httpx
from pydantic import BaseModel
from sqlalchemy import text
from app.database.base import engine, Base
from app.module.admin.router import router as admin_router
from app.module.users.router import router as users_router
from app.module.organization.router import router as organization_router
from app.module.role.router import router as role_router
from app.module.department.router import router as department_router
from app.module.document_type.router import router as document_type_router
from app.module.file_manage.router import router as file_manage_router
from app.module.draft_generation.router import router as draft_router
from app.module.auth.router import router as auth_router
from app.settings.config import settings
from app.utils.response import ErrorResponse

PIPELINE_DESCRIPTION = f"""
## Quantized Qwen Retrieval Pipeline

This backend uses the following runtime flow:

`FastAPI -> {settings.OLLAMA_EMBEDDING_MODEL} (Quantized) -> {settings.OLLAMA_EMBEDDING_DIMENSIONS}-dim Vector -> Qdrant -> Retriever -> {settings.OLLAMA_GENERATION_MODEL} (Quantized) -> Answer`

### Active Runtime Configuration

- Embedding provider: Ollama
- Embedding model: `{settings.OLLAMA_EMBEDDING_MODEL}`
- Embedding vector size: `{settings.OLLAMA_EMBEDDING_DIMENSIONS}`
- Vector database: Qdrant
- Retrieval step: semantic retriever over stored document chunks
- Generation provider: Ollama
- Generation model: `{settings.OLLAMA_GENERATION_MODEL}`
- Ollama base URL: `{settings.OLLAMA_BASE_URL}`

### Code Flow

1. FastAPI accepts the search or drafting request
2. `qwen3-embedding:8b` produces a quantized embedding vector
3. The full 4096-dimensional vector is stored and queried in Qdrant
4. The retriever fetches the most relevant chunks
5. `qwen3:8b` uses those chunks to generate the final answer

### Operational Notes

- Embeddings and generation both run through Ollama
- Qdrant collection sizing follows `OLLAMA_EMBEDDING_DIMENSIONS`
- Retrieval quality depends on the stored embedding dimension matching the active collection
- Changing vector size requires a matching Qdrant collection and re-indexed document vectors
"""

OPENAPI_TAGS = [
    {
        "name": "system",
        "description": "System-level service metadata, health, and LLM deployment guidance.",
    }
]


class PipelineInfo(BaseModel):
    title: str
    summary: str
    runtime_flow: str
    embedding_model: str
    embedding_dimensions: int
    vector_store: str
    retriever: str
    generation_model: str
    current_stack: dict[str, str | int]


class DependencyStatus(BaseModel):
    status: str
    detail: str | None = None


class SystemStatus(BaseModel):
    api: DependencyStatus
    database: DependencyStatus
    qdrant: DependencyStatus
    ollama: DependencyStatus


class OllamaModelInfo(BaseModel):
    name: str
    modified_at: str | None = None
    size: int | None = None


class OllamaModelsResponse(BaseModel):
    base_url: str
    generation_model: str
    embedding_model: str
    models: list[OllamaModelInfo]


class SystemOverview(BaseModel):
    pipeline: PipelineInfo
    status: SystemStatus
    ollama: OllamaModelsResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS designation VARCHAR(255)"))
        await conn.execute(text("ALTER TABLE organizations ADD COLUMN IF NOT EXISTS ai_provider VARCHAR(50) NOT NULL DEFAULT 'ollama'"))
        await conn.execute(text("ALTER TABLE organizations ADD COLUMN IF NOT EXISTS openai_api_key TEXT"))
        await conn.execute(text("ALTER TABLE organizations ADD COLUMN IF NOT EXISTS openai_embedding_model VARCHAR(255)"))
        await conn.execute(text("ALTER TABLE organizations ADD COLUMN IF NOT EXISTS openai_llm_model VARCHAR(255)"))
    yield


app = FastAPI(
    title="E-Abhilekh API",
    version="1.0.0",
    summary="FastAPI backend using a quantized Qwen embedding and generation pipeline with Qdrant retrieval.",
    description=PIPELINE_DESCRIPTION,
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
)

os.makedirs("previews", exist_ok=True)
app.mount("/previews", StaticFiles(directory="previews"), name="previews")

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(organization_router, prefix="/api/v1")
app.include_router(role_router, prefix="/api/v1")
app.include_router(department_router, prefix="/api/v1")
app.include_router(document_type_router, prefix="/api/v1")
app.include_router(file_manage_router, prefix="/api/v1")
app.include_router(draft_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(result=None, message=exc.detail, status_code=exc.status_code).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(result=None, message="Internal server error", status_code=500).model_dump(),
    )


@app.get(
    "/health",
    tags=["system"],
    responses={
        200: {
            "description": "Basic API liveness probe.",
            "content": {
                "application/json": {
                    "example": {"status": "ok"}
                }
            },
        }
    },
)
async def health():
    return {"status": "ok"}


@app.get(
    "/api/v1/system/pipeline",
    response_model=PipelineInfo,
    tags=["system"],
    responses={
        200: {
            "description": "Active quantized Qwen retrieval pipeline and current model configuration.",
            "content": {
                "application/json": {
                    "example": {
                        "title": "Quantized Qwen Retrieval Pipeline",
                        "summary": "FastAPI request flow using quantized Qwen embeddings, Qdrant retrieval, and quantized Qwen generation.",
                        "runtime_flow": "FastAPI -> qwen3-embedding:8b (Quantized) -> 4096 Vector -> Qdrant -> Retriever -> qwen3:8b (Quantized) -> Answer",
                        "embedding_model": settings.OLLAMA_EMBEDDING_MODEL,
                        "embedding_dimensions": settings.OLLAMA_EMBEDDING_DIMENSIONS,
                        "vector_store": "Qdrant",
                        "retriever": "Semantic retriever over document chunks",
                        "generation_model": settings.OLLAMA_GENERATION_MODEL,
                        "current_stack": {
                            "vector_store": "Qdrant",
                            "embedding_provider": "Ollama",
                            "embedding_model": settings.OLLAMA_EMBEDDING_MODEL,
                            "embedding_dimensions": settings.OLLAMA_EMBEDDING_DIMENSIONS,
                            "generation_provider": "Ollama",
                            "generation_model": settings.OLLAMA_GENERATION_MODEL,
                            "ollama_base_url": settings.OLLAMA_BASE_URL,
                        },
                    }
                }
            },
        }
    },
)
async def pipeline_info():
    return PipelineInfo(
        title="Quantized Qwen Retrieval Pipeline",
        summary="FastAPI request flow using quantized Qwen embeddings, Qdrant retrieval, and quantized Qwen generation.",
        runtime_flow="FastAPI -> qwen3-embedding:8b (Quantized) -> 4096 Vector -> Qdrant -> Retriever -> qwen3:8b (Quantized) -> Answer",
        embedding_model=settings.OLLAMA_EMBEDDING_MODEL,
        embedding_dimensions=settings.OLLAMA_EMBEDDING_DIMENSIONS,
        vector_store="Qdrant",
        retriever="Semantic retriever over document chunks",
        generation_model=settings.OLLAMA_GENERATION_MODEL,
        current_stack={
            "vector_store": "Qdrant",
            "embedding_provider": "Ollama",
            "embedding_model": settings.OLLAMA_EMBEDDING_MODEL,
            "embedding_dimensions": settings.OLLAMA_EMBEDDING_DIMENSIONS,
            "generation_provider": "Ollama",
            "generation_model": settings.OLLAMA_GENERATION_MODEL,
            "ollama_base_url": settings.OLLAMA_BASE_URL,
        },
    )


@app.get(
    "/api/v1/system/status",
    response_model=SystemStatus,
    tags=["system"],
    responses={
        200: {
            "description": "Runtime dependency health from the backend application layer.",
            "content": {
                "application/json": {
                    "example": {
                        "api": {"status": "ok", "detail": None},
                        "database": {"status": "ok", "detail": None},
                        "qdrant": {"status": "ok", "detail": None},
                        "ollama": {"status": "ok", "detail": None},
                    }
                }
            },
        }
    },
)
async def system_status():
    database = DependencyStatus(status="ok")
    qdrant = DependencyStatus(status="ok")
    ollama = DependencyStatus(status="ok")

    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        database = DependencyStatus(status="error", detail=str(exc))

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.QDRANT_URL}/healthz")
            response.raise_for_status()
    except Exception as exc:
        qdrant = DependencyStatus(status="error", detail=str(exc))

    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
    except Exception as exc:
        ollama = DependencyStatus(status="error", detail=str(exc))

    return SystemStatus(
        api=DependencyStatus(status="ok"),
        database=database,
        qdrant=qdrant,
        ollama=ollama,
    )


@app.get(
    "/api/v1/system/ollama/models",
    response_model=OllamaModelsResponse,
    tags=["system"],
    responses={
        200: {
            "description": "Available Ollama models exposed by the configured backend.",
            "content": {
                "application/json": {
                    "example": {
                        "base_url": settings.OLLAMA_BASE_URL,
                        "generation_model": settings.OLLAMA_GENERATION_MODEL,
                        "embedding_model": settings.OLLAMA_EMBEDDING_MODEL,
                        "models": [
                            {
                                "name": settings.OLLAMA_GENERATION_MODEL,
                                "modified_at": None,
                                "size": None,
                            }
                        ],
                    }
                }
            },
        }
    },
)
async def ollama_models():
    async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
        response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
        response.raise_for_status()

    payload = response.json()
    models = [
        OllamaModelInfo(
            name=model.get("name", ""),
            modified_at=model.get("modified_at"),
            size=model.get("size"),
        )
        for model in payload.get("models", [])
    ]

    return OllamaModelsResponse(
        base_url=settings.OLLAMA_BASE_URL,
        generation_model=settings.OLLAMA_GENERATION_MODEL,
        embedding_model=settings.OLLAMA_EMBEDDING_MODEL,
        models=models,
    )


@app.get(
    "/api/v1/system/overview",
    response_model=SystemOverview,
    tags=["system"],
    responses={
        200: {
            "description": "Combined pipeline configuration, runtime dependency health, and live Ollama model inventory.",
            "content": {
                "application/json": {
                    "example": {
                        "pipeline": {
                            "title": "Quantized Qwen Retrieval Pipeline",
                            "summary": "FastAPI request flow using quantized Qwen embeddings, Qdrant retrieval, and quantized Qwen generation.",
                            "runtime_flow": "FastAPI -> qwen3-embedding:8b (Quantized) -> 4096 Vector -> Qdrant -> Retriever -> qwen3:8b (Quantized) -> Answer",
                            "embedding_model": settings.OLLAMA_EMBEDDING_MODEL,
                            "embedding_dimensions": settings.OLLAMA_EMBEDDING_DIMENSIONS,
                            "vector_store": "Qdrant",
                            "retriever": "Semantic retriever over document chunks",
                            "generation_model": settings.OLLAMA_GENERATION_MODEL,
                            "current_stack": {
                                "vector_store": "Qdrant",
                                "embedding_provider": "Ollama",
                                "embedding_model": settings.OLLAMA_EMBEDDING_MODEL,
                                "embedding_dimensions": settings.OLLAMA_EMBEDDING_DIMENSIONS,
                                "generation_provider": "Ollama",
                                "generation_model": settings.OLLAMA_GENERATION_MODEL,
                                "ollama_base_url": settings.OLLAMA_BASE_URL,
                            },
                        },
                        "status": {
                            "api": {"status": "ok", "detail": None},
                            "database": {"status": "ok", "detail": None},
                            "qdrant": {"status": "ok", "detail": None},
                            "ollama": {"status": "ok", "detail": None},
                        },
                        "ollama": {
                            "base_url": settings.OLLAMA_BASE_URL,
                            "generation_model": settings.OLLAMA_GENERATION_MODEL,
                            "embedding_model": settings.OLLAMA_EMBEDDING_MODEL,
                            "models": [
                                {
                                    "name": settings.OLLAMA_GENERATION_MODEL,
                                    "modified_at": None,
                                    "size": None,
                                }
                            ],
                        },
                    }
                }
            },
        }
    },
)
async def system_overview():
    database = DependencyStatus(status="ok")
    qdrant = DependencyStatus(status="ok")
    ollama_status = DependencyStatus(status="ok")
    ollama_models_list: list[OllamaModelInfo] = []

    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        database = DependencyStatus(status="error", detail=str(exc))

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            qdrant_response = await client.get(f"{settings.QDRANT_URL}/healthz")
            qdrant_response.raise_for_status()
    except Exception as exc:
        qdrant = DependencyStatus(status="error", detail=str(exc))

    try:
        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
            ollama_response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            ollama_response.raise_for_status()
        payload = ollama_response.json()
        ollama_models_list = [
            OllamaModelInfo(
                name=model.get("name", ""),
                modified_at=model.get("modified_at"),
                size=model.get("size"),
            )
            for model in payload.get("models", [])
        ]
    except Exception as exc:
        ollama_status = DependencyStatus(status="error", detail=str(exc))

    pipeline = PipelineInfo(
        title="Quantized Qwen Retrieval Pipeline",
        summary="FastAPI request flow using quantized Qwen embeddings, Qdrant retrieval, and quantized Qwen generation.",
        runtime_flow="FastAPI -> qwen3-embedding:8b (Quantized) -> 4096 Vector -> Qdrant -> Retriever -> qwen3:8b (Quantized) -> Answer",
        embedding_model=settings.OLLAMA_EMBEDDING_MODEL,
        embedding_dimensions=settings.OLLAMA_EMBEDDING_DIMENSIONS,
        vector_store="Qdrant",
        retriever="Semantic retriever over document chunks",
        generation_model=settings.OLLAMA_GENERATION_MODEL,
        current_stack={
            "vector_store": "Qdrant",
            "embedding_provider": "Ollama",
            "embedding_model": settings.OLLAMA_EMBEDDING_MODEL,
            "embedding_dimensions": settings.OLLAMA_EMBEDDING_DIMENSIONS,
            "generation_provider": "Ollama",
            "generation_model": settings.OLLAMA_GENERATION_MODEL,
            "ollama_base_url": settings.OLLAMA_BASE_URL,
        },
    )

    return SystemOverview(
        pipeline=pipeline,
        status=SystemStatus(
            api=DependencyStatus(status="ok"),
            database=database,
            qdrant=qdrant,
            ollama=ollama_status,
        ),
        ollama=OllamaModelsResponse(
            base_url=settings.OLLAMA_BASE_URL,
            generation_model=settings.OLLAMA_GENERATION_MODEL,
            embedding_model=settings.OLLAMA_EMBEDDING_MODEL,
            models=ollama_models_list,
        ),
    )
