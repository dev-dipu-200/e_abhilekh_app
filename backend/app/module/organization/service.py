from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.user_model import Organization
from app.module.organization.schema import OrganizationCreate, OrganizationUpdate


async def get_organizations(db: AsyncSession, org_id: str | None = None):
    stmt = select(Organization)
    if org_id:
        stmt = stmt.where(Organization.id == org_id)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_organization(db: AsyncSession, org_id: str):
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    return result.scalar_one_or_none()


async def create_organization(db: AsyncSession, data: OrganizationCreate):
    existing = await db.execute(select(Organization).where(Organization.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="An organization with this name already exists")
    org = Organization(**data.model_dump())
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org


async def update_organization(db: AsyncSession, org_id: str, data: OrganizationUpdate):
    org = await get_organization(db, org_id)
    if not org:
        return None
    if data.name is not None and data.name != org.name:
        existing = await db.execute(select(Organization).where(Organization.name == data.name, Organization.id != org_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="An organization with this name already exists")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(org, key, val)
    await db.commit()
    await db.refresh(org)
    return org


async def delete_organization(db: AsyncSession, org_id: str):
    org = await get_organization(db, org_id)
    if not org:
        return False
    await db.delete(org)
    await db.commit()
    return True
