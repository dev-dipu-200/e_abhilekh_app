from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import get_db
from app.dependencies import get_current_user, get_current_superuser
from app.database.user_model import User
from app.module.organization.schema import OrganizationCreate, OrganizationUpdate, OrganizationResponse
from app.module.organization import service as org_service
from app.utils.response import SuccessResponse

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("/")
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_superuser:
        orgs = await org_service.get_organizations(db)
    else:
        orgs = await org_service.get_organizations(db, org_id=current_user.organization_id)
    return SuccessResponse(result=[OrganizationResponse.model_validate(o) for o in orgs], message="Organizations retrieved successfully", status_code=200)


@router.get("/{org_id}")
async def get_organization(
    org_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser and current_user.organization_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    org = await org_service.get_organization(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return SuccessResponse(result=OrganizationResponse.model_validate(org), message="Organization retrieved successfully", status_code=200)


@router.post("/", status_code=201)
async def create_organization(
    data: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    org = await org_service.create_organization(db, data)
    return SuccessResponse(result=OrganizationResponse.model_validate(org), message="Organization created successfully", status_code=201)


@router.put("/{org_id}")
async def update_organization(
    org_id: str,
    data: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    org = await org_service.update_organization(db, org_id, data)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return SuccessResponse(result=OrganizationResponse.model_validate(org), message="Organization updated successfully", status_code=200)


@router.delete("/{org_id}")
async def delete_organization(
    org_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    if not await org_service.delete_organization(db, org_id):
        raise HTTPException(status_code=404, detail="Organization not found")
    return SuccessResponse(result=None, message="Organization deleted successfully", status_code=200)
