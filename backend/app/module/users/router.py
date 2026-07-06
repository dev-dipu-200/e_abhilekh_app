from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import get_db
from app.module.users.schema import UserCreate, UserUpdate, UserResponse
from app.module.users import service as user_service
from app.dependencies import get_current_user, get_current_superuser
from app.database.user_model import User
from app.utils.response import SuccessResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/")
async def list_users(
    organization_id: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_superuser:
        page = await user_service.get_users(db, organization_id=organization_id, cursor=cursor, limit=limit)
    else:
        page = await user_service.get_users(
            db,
            organization_id=current_user.organization_id,
            cursor=cursor,
            limit=limit,
            exclude_superusers=True,
        )
    page.items = [UserResponse.model_validate(u) for u in page.items]
    return SuccessResponse(result=page, message="Users retrieved successfully", status_code=200)


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not current_user.is_superuser and current_user.organization_id != user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return SuccessResponse(result=UserResponse.model_validate(user), message="User retrieved successfully", status_code=200)


@router.post("/", status_code=201)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    user = await user_service.create_user(db, data)
    return SuccessResponse(result=UserResponse.model_validate(user), message="User created successfully", status_code=201)


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    user = await user_service.update_user(db, user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return SuccessResponse(result=UserResponse.model_validate(user), message="User updated successfully", status_code=200)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    if not await user_service.delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return SuccessResponse(result=None, message="User deleted successfully", status_code=200)
