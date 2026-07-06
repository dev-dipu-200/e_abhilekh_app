from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.file_model import DocumentType
from app.module.document_type.schema import DocumentTypeCreate, DocumentTypeUpdate
from app.utils.pagination import paginate_select


async def get_document_types(db: AsyncSession, organization_id: str | None = None, cursor: str | None = None, limit: int = 25):
    stmt = select(DocumentType)
    if organization_id:
        stmt = stmt.where(DocumentType.organization_id == organization_id)
    stmt = stmt.order_by(DocumentType.created_at.desc(), DocumentType.id.desc())
    return await paginate_select(db, stmt, cursor=cursor, limit=limit)


async def get_document_type(db: AsyncSession, doc_type_id: str):
    result = await db.execute(select(DocumentType).where(DocumentType.id == doc_type_id))
    return result.scalar_one_or_none()


async def create_document_type(db: AsyncSession, data: DocumentTypeCreate):
    existing = await db.execute(
        select(DocumentType).where(and_(DocumentType.name == data.name, DocumentType.organization_id == data.organization_id))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A document type with this name already exists in the organization")
    doc_type = DocumentType(**data.model_dump())
    db.add(doc_type)
    await db.commit()
    await db.refresh(doc_type)
    return doc_type


async def update_document_type(db: AsyncSession, doc_type_id: str, data: DocumentTypeUpdate):
    doc_type = await get_document_type(db, doc_type_id)
    if not doc_type:
        return None
    if data.name is not None and data.name != doc_type.name:
        existing = await db.execute(
            select(DocumentType).where(and_(DocumentType.name == data.name, DocumentType.organization_id == doc_type.organization_id, DocumentType.id != doc_type_id))
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="A document type with this name already exists in the organization")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(doc_type, key, val)
    await db.commit()
    await db.refresh(doc_type)
    return doc_type


async def delete_document_type(db: AsyncSession, doc_type_id: str):
    doc_type = await get_document_type(db, doc_type_id)
    if not doc_type:
        return False
    await db.delete(doc_type)
    await db.commit()
    return True
