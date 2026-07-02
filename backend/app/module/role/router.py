from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import get_db
from app.dependencies import get_current_user, get_current_superuser
from app.database.user_model import User
from app.module.role.schema import RoleCreate, RoleUpdate, RoleResponse
from app.module.role import service as role_service
from app.utils.response import SuccessResponse

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("/")
async def list_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_superuser:
        roles = await role_service.get_roles(db)
    else:
        roles = await role_service.get_roles(db, organization_id=current_user.organization_id)
    return SuccessResponse(result=[RoleResponse.model_validate(r) for r in roles], message="Roles retrieved successfully", status_code=200)


@router.get("/{role_id}")
async def get_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = await role_service.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if not current_user.is_superuser and role.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return SuccessResponse(result=RoleResponse.model_validate(role), message="Role retrieved successfully", status_code=200)


@router.post("/", status_code=201)
async def create_role(
    data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    role = await role_service.create_role(db, data)
    return SuccessResponse(result=RoleResponse.model_validate(role), message="Role created successfully", status_code=201)


@router.put("/{role_id}")
async def update_role(
    role_id: str,
    data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    role = await role_service.update_role(db, role_id, data)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return SuccessResponse(result=RoleResponse.model_validate(role), message="Role updated successfully", status_code=200)


@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    if not await role_service.delete_role(db, role_id):
        raise HTTPException(status_code=404, detail="Role not found")
    return SuccessResponse(result=None, message="Role deleted successfully", status_code=200)
