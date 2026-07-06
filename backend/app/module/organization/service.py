from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.file_model import Document
from app.database.user_model import Organization
from app.module.organization.schema import OrganizationCreate, OrganizationUpdate
from app.module.file_manage.tasks import process_document_file
from app.utils.pagination import paginate_select
from app.utils.ai_runtime import resolve_org_ai_config


def _normalize_openai_key(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _validate_ai_config(
    *,
    ai_provider: str,
    openai_api_key: str | None,
    openai_embedding_model: str | None,
    openai_llm_model: str | None,
) -> None:
    if ai_provider != "openai":
        return
    if not openai_api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key is required when AI provider is OpenAI")
    if not openai_embedding_model:
        raise HTTPException(status_code=400, detail="OpenAI embedding model is required when AI provider is OpenAI")
    if not openai_llm_model:
        raise HTTPException(status_code=400, detail="OpenAI LLM model is required when AI provider is OpenAI")


async def _enqueue_reindex_for_organization(db: AsyncSession, org_id: str) -> None:
    result = await db.execute(select(Document.id).where(Document.organization_id == org_id))
    for document_id in result.scalars().all():
        process_document_file.delay(document_id)


async def get_organizations(db: AsyncSession, org_id: str | None = None, cursor: str | None = None, limit: int = 25):
    stmt = select(Organization)
    if org_id:
        stmt = stmt.where(Organization.id == org_id)
    stmt = stmt.order_by(Organization.created_at.desc(), Organization.id.desc())
    return await paginate_select(db, stmt, cursor=cursor, limit=limit)


async def get_organization(db: AsyncSession, org_id: str):
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    return result.scalar_one_or_none()


async def create_organization(db: AsyncSession, data: OrganizationCreate):
    existing = await db.execute(select(Organization).where(Organization.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="An organization with this name already exists")
    payload = data.model_dump()
    payload["ai_provider"] = (payload.get("ai_provider") or "ollama").strip().lower()
    payload["openai_api_key"] = _normalize_openai_key(payload.get("openai_api_key"))
    payload["openai_embedding_model"] = (payload.get("openai_embedding_model") or "").strip() or None
    payload["openai_llm_model"] = (payload.get("openai_llm_model") or "").strip() or None
    _validate_ai_config(
        ai_provider=payload["ai_provider"],
        openai_api_key=payload.get("openai_api_key"),
        openai_embedding_model=payload.get("openai_embedding_model"),
        openai_llm_model=payload.get("openai_llm_model"),
    )
    org = Organization(**payload)
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org


async def update_organization(db: AsyncSession, org_id: str, data: OrganizationUpdate):
    org = await get_organization(db, org_id)
    if not org:
        return None
    old_runtime = resolve_org_ai_config(org, org.id)
    if data.name is not None and data.name != org.name:
        existing = await db.execute(select(Organization).where(Organization.name == data.name, Organization.id != org_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="An organization with this name already exists")

    update_data = data.model_dump(exclude_unset=True)
    if "ai_provider" in update_data and update_data["ai_provider"] is not None:
        update_data["ai_provider"] = update_data["ai_provider"].strip().lower()
    if "openai_api_key" in update_data:
        update_data["openai_api_key"] = _normalize_openai_key(update_data["openai_api_key"])
    if "openai_embedding_model" in update_data:
        update_data["openai_embedding_model"] = (update_data["openai_embedding_model"] or "").strip() or None
    if "openai_llm_model" in update_data:
        update_data["openai_llm_model"] = (update_data["openai_llm_model"] or "").strip() or None

    clear_api_key = bool(update_data.pop("clear_openai_api_key", False))
    effective_provider = update_data.get("ai_provider", org.ai_provider or "ollama")
    effective_api_key = update_data.get("openai_api_key", org.openai_api_key)
    effective_embedding_model = update_data.get("openai_embedding_model", org.openai_embedding_model)
    effective_llm_model = update_data.get("openai_llm_model", org.openai_llm_model)

    if clear_api_key:
        effective_api_key = None
        org.openai_api_key = None

    _validate_ai_config(
        ai_provider=effective_provider,
        openai_api_key=effective_api_key,
        openai_embedding_model=effective_embedding_model,
        openai_llm_model=effective_llm_model,
    )

    for key, val in update_data.items():
        setattr(org, key, val)
    await db.commit()
    await db.refresh(org)
    new_runtime = resolve_org_ai_config(org, org.id)
    if (
        old_runtime.provider != new_runtime.provider
        or old_runtime.embedding_model != new_runtime.embedding_model
        or old_runtime.embedding_dimensions != new_runtime.embedding_dimensions
    ):
        await _enqueue_reindex_for_organization(db, org.id)
    return org


async def delete_organization(db: AsyncSession, org_id: str):
    org = await get_organization(db, org_id)
    if not org:
        return False
    await db.delete(org)
    await db.commit()
    return True
