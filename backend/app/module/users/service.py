import bcrypt
from fastapi import HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.user_model import User
from app.module.users.schema import UserCreate, UserUpdate
from app.utils.pagination import paginate_select


async def get_users(
    db: AsyncSession,
    organization_id: str | None = None,
    cursor: str | None = None,
    limit: int = 25,
    exclude_superusers: bool = False,
):
    stmt = select(User)
    if organization_id:
        stmt = stmt.where(User.organization_id == organization_id)
    if exclude_superusers:
        stmt = stmt.where(User.is_superuser.is_(False))
    stmt = stmt.order_by(User.created_at.desc(), User.id.desc())
    return await paginate_select(db, stmt, cursor=cursor, limit=limit)


async def get_user(db: AsyncSession, user_id: str):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, data: UserCreate):
    existing = await db.execute(
        select(User).where(or_(User.email == data.email, User.username == data.username))
    )
    existing_user = existing.scalar_one_or_none()
    if existing_user:
        if existing_user.email == data.email:
            raise HTTPException(status_code=409, detail="A user with this email already exists")
        raise HTTPException(status_code=409, detail="A user with this username already exists")
    user = User(
        email=data.email,
        username=data.username,
        full_name=data.full_name,
        employee_id=data.employee_id,
        organization_id=data.organization_id,
        role_id=data.role_id,
        is_active=data.is_active,
        hashed_password=bcrypt.hashpw(data.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user_id: str, data: UserUpdate):
    user = await get_user(db, user_id)
    if not user:
        return None
    if data.email is not None and data.email != user.email:
        existing = await db.execute(select(User).where(User.email == data.email, User.id != user_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="A user with this email already exists")
    if data.username is not None and data.username != user.username:
        existing = await db.execute(select(User).where(User.username == data.username, User.id != user_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="A user with this username already exists")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(user, key, val)
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: str):
    user = await get_user(db, user_id)
    if not user:
        return False
    await db.delete(user)
    await db.commit()
    return True
