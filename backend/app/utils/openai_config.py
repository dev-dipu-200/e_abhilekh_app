from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.user_model import Organization, User


def normalize_openai_key(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def normalize_model_name(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def validate_openai_model_pair(
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
    if openai_embedding_model.casefold() == openai_llm_model.casefold():
        raise HTTPException(status_code=409, detail="OpenAI embedding model and LLM model must be different")


async def ensure_unique_openai_api_key(
    db: AsyncSession,
    *,
    openai_api_key: str | None,
    exclude_organization_id: str | None = None,
    exclude_user_id: str | None = None,
) -> None:
    if not openai_api_key:
        return

    org_stmt = select(Organization.id, Organization.name).where(Organization.openai_api_key == openai_api_key)
    if exclude_organization_id:
        org_stmt = org_stmt.where(Organization.id != exclude_organization_id)
    org_match = (await db.execute(org_stmt)).first()
    if org_match:
        raise HTTPException(
            status_code=409,
            detail=f"OpenAI API key is already configured for organization '{org_match.name}'",
        )

    user_stmt = select(User.id, User.email).where(User.openai_api_key == openai_api_key)
    if exclude_user_id:
        user_stmt = user_stmt.where(User.id != exclude_user_id)
    user_match = (await db.execute(user_stmt)).first()
    if user_match:
        raise HTTPException(
            status_code=409,
            detail=f"OpenAI API key is already configured for user '{user_match.email}'",
        )
