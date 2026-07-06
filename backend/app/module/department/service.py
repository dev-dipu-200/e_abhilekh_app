from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.file_model import Department
from app.module.department.schema import DepartmentCreate, DepartmentUpdate
from app.utils.pagination import paginate_select


async def get_departments(db: AsyncSession, organization_id: str | None = None, cursor: str | None = None, limit: int = 25):
    stmt = select(Department)
    if organization_id:
        stmt = stmt.where(Department.organization_id == organization_id)
    stmt = stmt.order_by(Department.created_at.desc(), Department.id.desc())
    return await paginate_select(db, stmt, cursor=cursor, limit=limit)


async def get_department(db: AsyncSession, dept_id: str):
    result = await db.execute(select(Department).where(Department.id == dept_id))
    return result.scalar_one_or_none()


async def create_department(db: AsyncSession, data: DepartmentCreate):
    existing = await db.execute(
        select(Department).where(and_(Department.name == data.name, Department.organization_id == data.organization_id))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A department with this name already exists in the organization")
    dept = Department(**data.model_dump())
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept


async def update_department(db: AsyncSession, dept_id: str, data: DepartmentUpdate):
    dept = await get_department(db, dept_id)
    if not dept:
        return None
    if data.name is not None and data.name != dept.name:
        existing = await db.execute(
            select(Department).where(and_(Department.name == data.name, Department.organization_id == dept.organization_id, Department.id != dept_id))
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="A department with this name already exists in the organization")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(dept, key, val)
    await db.commit()
    await db.refresh(dept)
    return dept


async def delete_department(db: AsyncSession, dept_id: str):
    dept = await get_department(db, dept_id)
    if not dept:
        return False
    await db.delete(dept)
    await db.commit()
    return True
