import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.file_model import Document
from app.database.user_model import Organization


def build_file_number_prefix(org_name: str | None) -> str:
    base = re.sub(r"[^A-Za-z0-9]+", "_", (org_name or "ORG").strip().upper()).strip("_")
    return base or "ORG"


async def generate_file_number(db: AsyncSession, organization_id: str) -> str:
    org_result = await db.execute(select(Organization).where(Organization.id == organization_id))
    organization = org_result.scalar_one_or_none()
    prefix = build_file_number_prefix(organization.name if organization else organization_id)
    pattern = f"{prefix}_F%"

    existing_result = await db.execute(
        select(Document.file_number)
        .where(
            Document.organization_id == organization_id,
            Document.file_number.is_not(None),
            Document.file_number.like(pattern),
        )
        .order_by(Document.file_number.desc())
        .limit(1)
    )
    last_file_number = existing_result.scalar_one_or_none()
    next_number = 1
    if last_file_number:
        try:
            next_number = int(last_file_number.rsplit("_F", 1)[1]) + 1
        except (IndexError, ValueError):
            next_number = 1
    return f"{prefix}_F{next_number:08d}"
