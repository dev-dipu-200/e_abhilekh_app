from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import get_db
from app.dependencies import get_current_user, get_current_superuser, get_current_org_admin
from app.database.user_model import User
from app.module.organization.schema import OrganizationCreate, OrganizationUpdate, OrganizationResponse
from app.module.organization import service as org_service
from app.utils.response import SuccessResponse

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def _to_response(org) -> OrganizationResponse:
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        address=org.address,
        is_active=org.is_active,
        ai_provider=org.ai_provider or "ollama",
        openai_embedding_model=org.openai_embedding_model,
        openai_llm_model=org.openai_llm_model,
        has_openai_api_key=bool(org.openai_api_key),
        created_at=org.created_at,
    )


@router.get("/")
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_superuser:
        orgs = await org_service.get_organizations(db)
    else:
        orgs = await org_service.get_organizations(db, org_id=current_user.organization_id)
    return SuccessResponse(result=[_to_response(o) for o in orgs], message="Organizations retrieved successfully", status_code=200)


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
    return SuccessResponse(result=_to_response(org), message="Organization retrieved successfully", status_code=200)


@router.post("/", status_code=201)
async def create_organization(
    data: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    org = await org_service.create_organization(db, data)
    return SuccessResponse(result=_to_response(org), message="Organization created successfully", status_code=201)


@router.put("/{org_id}")
async def update_organization(
    org_id: str,
    data: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_org_admin),
):
    if not current_user.is_superuser and current_user.organization_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    org = await org_service.update_organization(db, org_id, data)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return SuccessResponse(result=_to_response(org), message="Organization updated successfully", status_code=200)


@router.delete("/{org_id}")
async def delete_organization(
    org_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    if not await org_service.delete_organization(db, org_id):
        raise HTTPException(status_code=404, detail="Organization not found")
    return SuccessResponse(result=None, message="Organization deleted successfully", status_code=200)
