import aiofiles
import os
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import get_db
from app.dependencies import get_current_user
from app.database.user_model import User
from app.module.file_manage.schema import DocumentCreate, DocumentUpdate, DocumentResponse, FolderCreate, FolderResponse, SearchQuery, SearchResponse
from app.module.file_manage import service as file_service
from app.module.file_manage.tasks import process_document_file, generate_document_preview
from app.utils.response import SuccessResponse

router = APIRouter(prefix="/files", tags=["File Management"])


@router.get("/documents")
async def list_documents(organization_id: str, folder_id: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    docs = await file_service.get_documents(db, organization_id, folder_id)
    return SuccessResponse(result=[DocumentResponse.model_validate(d) for d in docs], message="Documents retrieved successfully", status_code=200)


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await file_service.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return SuccessResponse(result=DocumentResponse.model_validate(doc), message="Document retrieved successfully", status_code=200)


@router.post("/documents", status_code=201)
async def upload_document(
    organization_id: str = Query(...),
    department_id: str = Query(...),
    document_type_id: str = Query(...),
    subject: str = Query(...),
    folder_id: str | None = Query(None),
    parser_type: str | None = Query(None),
    designation: str | None = Query(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    upload_dir = f"files/{organization_id}/"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename or "untitled.pdf")
    content = await file.read()
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    doc_data = DocumentCreate(
        organization_id=organization_id,
        department_id=department_id,
        document_type_id=document_type_id,
        folder_id=folder_id,
        parser_type=parser_type,
        designation=designation,
        subject=subject,
    )
    doc = await file_service.create_document(db, doc_data, uploader_id=current_user.id, file_path=file_path)
    process_document_file.delay(doc.id)
    generate_document_preview.delay(doc.id)
    return SuccessResponse(result=DocumentResponse.model_validate(doc), message="Document uploaded successfully", status_code=201)


@router.put("/documents/{doc_id}")
async def update_document(doc_id: str, data: DocumentUpdate, db: AsyncSession = Depends(get_db)):
    doc = await file_service.update_document(db, doc_id, data)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return SuccessResponse(result=DocumentResponse.model_validate(doc), message="Document updated successfully", status_code=200)


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    if not await file_service.delete_document(db, doc_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return SuccessResponse(result=None, message="Document deleted successfully", status_code=200)


@router.get("/folders")
async def list_folders(organization_id: str, parent_id: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    folders = await file_service.get_folders(db, organization_id, parent_id)
    return SuccessResponse(result=[FolderResponse.model_validate(f) for f in folders], message="Folders retrieved successfully", status_code=200)


@router.post("/folders", status_code=201)
async def create_folder(data: FolderCreate, db: AsyncSession = Depends(get_db)):
    folder = await file_service.create_folder(db, data, user_id="")
    return SuccessResponse(result=FolderResponse.model_validate(folder), message="Folder created successfully", status_code=201)


@router.post("/search")
async def search_documents(data: SearchQuery, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    results = await file_service.search_documents(db, data.query, data.organization_id, data.limit)
    return SuccessResponse(result=SearchResponse(query=data.query, language=data.language, results=results), message="Search completed", status_code=200)


@router.delete("/folders/{folder_id}")
async def delete_folder(folder_id: str, db: AsyncSession = Depends(get_db)):
    if not await file_service.delete_folder(db, folder_id):
        raise HTTPException(status_code=404, detail="Folder not found")
    return SuccessResponse(result=None, message="Folder deleted successfully", status_code=200)
