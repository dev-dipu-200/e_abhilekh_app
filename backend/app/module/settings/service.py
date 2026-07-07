from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.file_model import Document
from app.database.user_model import Organization, User
from app.module.file_manage.tasks import process_document_file
from app.module.settings.schema import AISettingsUpdate
from app.utils.ai_runtime import resolve_ai_config
from app.utils.openai_config import (
    ensure_unique_openai_api_key,
    normalize_model_name,
    normalize_openai_key,
    validate_openai_model_pair,
)


async def get_ai_settings(db: AsyncSession, current_user: User):
    org_result = await db.execute(select(Organization).where(Organization.id == current_user.organization_id))
    organization = org_result.scalar_one_or_none()
    return {
        "ai_provider": current_user.ai_provider or "ollama",
        "openai_embedding_model": current_user.openai_embedding_model,
        "openai_llm_model": current_user.openai_llm_model,
        "has_openai_api_key": bool(current_user.openai_api_key),
        "organization_ai_provider": organization.ai_provider if organization else "ollama",
        "organization_openai_embedding_model": organization.openai_embedding_model if organization else None,
        "organization_openai_llm_model": organization.openai_llm_model if organization else None,
        "organization_has_openai_api_key": bool(organization.openai_api_key) if organization else False,
    }


async def update_ai_settings(db: AsyncSession, current_user: User, data: AISettingsUpdate):
    org_result = await db.execute(select(Organization).where(Organization.id == current_user.organization_id))
    organization = org_result.scalar_one_or_none()
    old_runtime = resolve_ai_config(organization, current_user.organization_id, current_user)

    update_data = data.model_dump(exclude_unset=True)
    provider = (update_data.get("ai_provider") or current_user.ai_provider or "ollama").strip().lower()
    api_key = normalize_openai_key(update_data.get("openai_api_key", current_user.openai_api_key))
    embedding_model = normalize_model_name(update_data.get("openai_embedding_model", current_user.openai_embedding_model))
    llm_model = normalize_model_name(update_data.get("openai_llm_model", current_user.openai_llm_model))

    if update_data.get("clear_openai_api_key"):
        api_key = None

    validate_openai_model_pair(
        ai_provider=provider,
        openai_api_key=api_key,
        openai_embedding_model=embedding_model,
        openai_llm_model=llm_model,
    )
    await ensure_unique_openai_api_key(
        db,
        openai_api_key=api_key,
        exclude_user_id=current_user.id,
    )

    current_user.ai_provider = provider
    current_user.openai_api_key = api_key
    current_user.openai_embedding_model = embedding_model if provider == "openai" else None
    current_user.openai_llm_model = llm_model if provider == "openai" else None
    await db.commit()
    await db.refresh(current_user)

    new_runtime = resolve_ai_config(organization, current_user.organization_id, current_user)
    if (
        old_runtime.provider != new_runtime.provider
        or old_runtime.embedding_model != new_runtime.embedding_model
        or old_runtime.embedding_dimensions != new_runtime.embedding_dimensions
    ):
        result = await db.execute(select(Document.id).where(Document.organization_id == current_user.organization_id))
        for document_id in result.scalars().all():
            process_document_file.delay(document_id)

    return await get_ai_settings(db, current_user)
