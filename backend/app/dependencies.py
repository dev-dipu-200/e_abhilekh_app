from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import get_db
from app.module.auth.service import get_user_from_token
from app.database.user_model import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await get_user_from_token(db, credentials.credentials)


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def get_current_org_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.is_superuser:
        return current_user
    if current_user.role and (current_user.role.is_admin or current_user.role.is_superadmin):
        return current_user
    raise HTTPException(status_code=403, detail="Organization admin access required")
