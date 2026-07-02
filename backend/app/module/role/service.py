from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.user_model import Role
from app.module.role.schema import RoleCreate, RoleUpdate


async def get_roles(db: AsyncSession, organization_id: str | None = None):
    stmt = select(Role)
    if organization_id:
        stmt = stmt.where(Role.organization_id == organization_id)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_role(db: AsyncSession, role_id: str):
    result = await db.execute(select(Role).where(Role.id == role_id))
    return result.scalar_one_or_none()


async def create_role(db: AsyncSession, data: RoleCreate):
    existing = await db.execute(
        select(Role).where(and_(Role.name == data.name, Role.organization_id == data.organization_id))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A role with this name already exists in the organization")
    role = Role(**data.model_dump())
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


async def update_role(db: AsyncSession, role_id: str, data: RoleUpdate):
    role = await get_role(db, role_id)
    if not role:
        return None
    if data.name is not None and data.name != role.name:
        existing = await db.execute(
            select(Role).where(and_(Role.name == data.name, Role.organization_id == role.organization_id, Role.id != role_id))
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="A role with this name already exists in the organization")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(role, key, val)
    await db.commit()
    await db.refresh(role)
    return role


async def delete_role(db: AsyncSession, role_id: str):
    role = await get_role(db, role_id)
    if not role:
        return False
    await db.delete(role)
    await db.commit()
    return True
