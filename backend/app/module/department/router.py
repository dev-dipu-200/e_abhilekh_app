from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import get_db
from app.dependencies import get_current_user, get_current_superuser
from app.database.user_model import User
from app.module.department.schema import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from app.module.department import service as dept_service
from app.utils.response import SuccessResponse

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("/")
async def list_departments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_superuser:
        depts = await dept_service.get_departments(db)
    else:
        depts = await dept_service.get_departments(db, organization_id=current_user.organization_id)
    return SuccessResponse(result=[DepartmentResponse.model_validate(d) for d in depts], message="Departments retrieved successfully", status_code=200)


@router.get("/{dept_id}")
async def get_department(
    dept_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dept = await dept_service.get_department(db, dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    if not current_user.is_superuser and dept.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return SuccessResponse(result=DepartmentResponse.model_validate(dept), message="Department retrieved successfully", status_code=200)


@router.post("/", status_code=201)
async def create_department(
    data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    dept = await dept_service.create_department(db, data)
    return SuccessResponse(result=DepartmentResponse.model_validate(dept), message="Department created successfully", status_code=201)


@router.put("/{dept_id}")
async def update_department(
    dept_id: str,
    data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    dept = await dept_service.update_department(db, dept_id, data)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return SuccessResponse(result=DepartmentResponse.model_validate(dept), message="Department updated successfully", status_code=200)


@router.delete("/{dept_id}")
async def delete_department(
    dept_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    if not await dept_service.delete_department(db, dept_id):
        raise HTTPException(status_code=404, detail="Department not found")
    return SuccessResponse(result=None, message="Department deleted successfully", status_code=200)
