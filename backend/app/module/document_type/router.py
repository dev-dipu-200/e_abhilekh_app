from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import get_db
from app.dependencies import get_current_user, get_current_superuser
from app.database.user_model import User
from app.module.document_type.schema import DocumentTypeCreate, DocumentTypeUpdate, DocumentTypeResponse
from app.module.document_type import service as doc_type_service
from app.utils.response import SuccessResponse

router = APIRouter(prefix="/document-types", tags=["Document Types"])


@router.get("/")
async def list_document_types(
    organization_id: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_superuser:
        page = await doc_type_service.get_document_types(db, organization_id=organization_id, cursor=cursor, limit=limit)
    else:
        page = await doc_type_service.get_document_types(db, organization_id=current_user.organization_id, cursor=cursor, limit=limit)
    page.items = [DocumentTypeResponse.model_validate(d) for d in page.items]
    return SuccessResponse(result=page, message="Document types retrieved successfully", status_code=200)


@router.get("/{doc_type_id}")
async def get_document_type(
    doc_type_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc_type = await doc_type_service.get_document_type(db, doc_type_id)
    if not doc_type:
        raise HTTPException(status_code=404, detail="Document type not found")
    if not current_user.is_superuser and doc_type.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return SuccessResponse(result=DocumentTypeResponse.model_validate(doc_type), message="Document type retrieved successfully", status_code=200)


@router.post("/", status_code=201)
async def create_document_type(
    data: DocumentTypeCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    doc_type = await doc_type_service.create_document_type(db, data)
    return SuccessResponse(result=DocumentTypeResponse.model_validate(doc_type), message="Document type created successfully", status_code=201)


@router.put("/{doc_type_id}")
async def update_document_type(
    doc_type_id: str,
    data: DocumentTypeUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    doc_type = await doc_type_service.update_document_type(db, doc_type_id, data)
    if not doc_type:
        raise HTTPException(status_code=404, detail="Document type not found")
    return SuccessResponse(result=DocumentTypeResponse.model_validate(doc_type), message="Document type updated successfully", status_code=200)


@router.delete("/{doc_type_id}")
async def delete_document_type(
    doc_type_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    if not await doc_type_service.delete_document_type(db, doc_type_id):
        raise HTTPException(status_code=404, detail="Document type not found")
    return SuccessResponse(result=None, message="Document type deleted successfully", status_code=200)
