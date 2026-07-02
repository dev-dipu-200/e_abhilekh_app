import bcrypt
from fastapi import HTTPException
from sqlalchemy import select, func, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.user_model import Organization, User, Role
from app.database.file_model import Document, Department, DocumentType, Folder, Note, Attachment, ActivityLog, GeneratedDraft


async def get_dashboard_stats(db: AsyncSession):
    orgs = await db.execute(select(func.count(Organization.id)))
    users = await db.execute(select(func.count(User.id)))
    docs = await db.execute(select(func.count(Document.id)))
    depts = await db.execute(select(func.count(Department.id)))
    return {
        "total_organizations": orgs.scalar(),
        "total_users": users.scalar(),
        "total_documents": docs.scalar(),
        "total_departments": depts.scalar(),
    }


async def register_admin(db: AsyncSession, email: str, username: str, password: str, full_name: str | None = None):
    existing = await db.execute(
        select(User).where(or_(User.email == email, User.username == username))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A user with this email or username already exists")

    org = await db.execute(select(Organization).limit(1))
    org = org.scalar_one_or_none()
    if not org:
        org = Organization(name="Default Organization")
        db.add(org)
        await db.flush()

    role = await db.execute(select(Role).where(Role.is_superadmin == True).limit(1))
    role = role.scalar_one_or_none()
    if not role:
        role = Role(name="Super Admin", organization_id=org.id, is_superadmin=True, is_admin=True)
        db.add(role)
        await db.flush()

    user = User(
        email=email,
        username=username,
        full_name=full_name,
        organization_id=org.id,
        role_id=role.id,
        is_superuser=True,
        is_active=True,
        hashed_password=bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def clear_all_records(db: AsyncSession):
    tables = [
        ActivityLog.__tablename__,
        GeneratedDraft.__tablename__,
        Attachment.__tablename__,
        Note.__tablename__,
        Document.__tablename__,
        Folder.__tablename__,
        DocumentType.__tablename__,
        Department.__tablename__,
        User.__tablename__,
        Role.__tablename__,
        Organization.__tablename__,
    ]
    for table in tables:
        await db.execute(text(f"DELETE FROM {table}"))
    await db.commit()



