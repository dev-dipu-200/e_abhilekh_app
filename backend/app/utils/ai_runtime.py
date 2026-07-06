from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.database.user_model import Organization, User
from app.settings.config import settings


OPENAI_EMBEDDING_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


@dataclass(frozen=True)
class AIRuntimeConfig:
    organization_id: str
    scope_type: str
    scope_id: str
    provider: str
    embedding_model: str
    generation_model: str
    embedding_dimensions: int
    collection_name: str
    user_id: str | None = None
    openai_api_key: str | None = None
    ollama_base_url: str | None = None


def get_openai_embedding_dimensions(model: str | None) -> int:
    if not model:
        return 1536
    return OPENAI_EMBEDDING_DIMENSIONS.get(model.strip(), 1536)


def _build_collection_name(collection_scope: str, provider: str, embedding_model: str, dimensions: int) -> str:
    safe_scope = re.sub(r"[^a-zA-Z0-9_]+", "_", collection_scope).strip("_").lower() or "scope"
    signature = hashlib.sha1(f"{provider}:{embedding_model}:{dimensions}".encode("utf-8")).hexdigest()[:12]
    return f"documents_{safe_scope}_{signature}"


def _has_openai_config(entity: Organization | User | None) -> bool:
    provider = (getattr(entity, "ai_provider", None) or "ollama").strip().lower() if entity else "ollama"
    return bool(
        provider == "openai"
        and getattr(entity, "openai_api_key", None)
        and getattr(entity, "openai_embedding_model", None)
        and getattr(entity, "openai_llm_model", None)
    )


def _resolve_openai_runtime(
    *,
    organization_id: str,
    scope_type: str,
    scope_id: str,
    user_id: str | None,
    api_key: str,
    embedding_model: str,
    generation_model: str,
) -> AIRuntimeConfig:
    dimensions = get_openai_embedding_dimensions(embedding_model)
    return AIRuntimeConfig(
        organization_id=organization_id,
        scope_type=scope_type,
        scope_id=scope_id,
        user_id=user_id,
        provider="openai",
        embedding_model=embedding_model,
        generation_model=generation_model,
        embedding_dimensions=dimensions,
        collection_name=_build_collection_name(scope_id, "openai", embedding_model, dimensions),
        openai_api_key=api_key,
    )


def resolve_ai_config(org: Organization | None, organization_id: str, user: User | None = None) -> AIRuntimeConfig:
    if _has_openai_config(user):
        return _resolve_openai_runtime(
            organization_id=organization_id,
            scope_type="user",
            scope_id=user.id,
            user_id=user.id,
            api_key=user.openai_api_key.strip(),
            embedding_model=user.openai_embedding_model.strip(),
            generation_model=user.openai_llm_model.strip(),
        )

    if _has_openai_config(org):
        return _resolve_openai_runtime(
            organization_id=organization_id,
            scope_type="organization",
            scope_id=organization_id,
            user_id=None,
            api_key=org.openai_api_key.strip(),
            embedding_model=org.openai_embedding_model.strip(),
            generation_model=org.openai_llm_model.strip(),
        )

    embedding_model = settings.OLLAMA_EMBEDDING_MODEL
    generation_model = settings.OLLAMA_GENERATION_MODEL
    dimensions = settings.OLLAMA_EMBEDDING_DIMENSIONS
    return AIRuntimeConfig(
        organization_id=organization_id,
        scope_type="organization",
        scope_id=organization_id,
        provider="ollama",
        embedding_model=embedding_model,
        generation_model=generation_model,
        embedding_dimensions=dimensions,
        collection_name=_build_collection_name(organization_id, "ollama", embedding_model, dimensions),
        ollama_base_url=settings.OLLAMA_BASE_URL,
    )


def resolve_org_ai_config(org: Organization | None, organization_id: str) -> AIRuntimeConfig:
    return resolve_ai_config(org, organization_id)
