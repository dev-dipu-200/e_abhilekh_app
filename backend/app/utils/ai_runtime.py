from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.database.user_model import Organization
from app.settings.config import settings


OPENAI_EMBEDDING_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


@dataclass(frozen=True)
class AIRuntimeConfig:
    organization_id: str
    provider: str
    embedding_model: str
    generation_model: str
    embedding_dimensions: int
    collection_name: str
    openai_api_key: str | None = None
    ollama_base_url: str | None = None


def get_openai_embedding_dimensions(model: str | None) -> int:
    if not model:
        return 1536
    return OPENAI_EMBEDDING_DIMENSIONS.get(model.strip(), 1536)


def _build_collection_name(organization_id: str, provider: str, embedding_model: str, dimensions: int) -> str:
    safe_org = re.sub(r"[^a-zA-Z0-9_]+", "_", organization_id).strip("_").lower() or "org"
    signature = hashlib.sha1(f"{provider}:{embedding_model}:{dimensions}".encode("utf-8")).hexdigest()[:12]
    return f"documents_{safe_org}_{signature}"


def resolve_org_ai_config(org: Organization | None, organization_id: str) -> AIRuntimeConfig:
    provider = (getattr(org, "ai_provider", None) or "ollama").strip().lower()

    if (
        provider == "openai"
        and getattr(org, "openai_api_key", None)
        and getattr(org, "openai_embedding_model", None)
        and getattr(org, "openai_llm_model", None)
    ):
        embedding_model = org.openai_embedding_model.strip()
        generation_model = org.openai_llm_model.strip()
        dimensions = get_openai_embedding_dimensions(embedding_model)
        return AIRuntimeConfig(
            organization_id=organization_id,
            provider="openai",
            embedding_model=embedding_model,
            generation_model=generation_model,
            embedding_dimensions=dimensions,
            collection_name=_build_collection_name(organization_id, "openai", embedding_model, dimensions),
            openai_api_key=org.openai_api_key,
        )

    embedding_model = settings.OLLAMA_EMBEDDING_MODEL
    generation_model = settings.OLLAMA_GENERATION_MODEL
    dimensions = settings.OLLAMA_EMBEDDING_DIMENSIONS
    return AIRuntimeConfig(
        organization_id=organization_id,
        provider="ollama",
        embedding_model=embedding_model,
        generation_model=generation_model,
        embedding_dimensions=dimensions,
        collection_name=_build_collection_name(organization_id, "ollama", embedding_model, dimensions),
        ollama_base_url=settings.OLLAMA_BASE_URL,
    )

