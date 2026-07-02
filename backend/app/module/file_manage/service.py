import time
from fastapi import HTTPException
from sqlalchemy import select, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
import uuid
from app.database.file_model import Document, Folder, Department, DocumentType, ProcessingState
from app.module.file_manage.schema import DocumentCreate, DocumentUpdate, FolderCreate, SearchResultItem
from app.utils.qdrant_store import search as qdrant_search


async def get_documents(db: AsyncSession, organization_id: str, folder_id: str | None = None):
    stmt = select(Document).where(Document.organization_id == organization_id)
    if folder_id:
        stmt = stmt.where(Document.folder_id == folder_id)
    stmt = stmt.order_by(Document.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_document(db: AsyncSession, doc_id: str):
    result = await db.execute(
        select(Document).options(
            joinedload(Document.department),
            joinedload(Document.document_type),
            joinedload(Document.folder),
        ).where(Document.id == doc_id)
    )
    return result.unique().scalar_one_or_none()


async def create_document(db: AsyncSession, data: DocumentCreate, uploader_id: str, file_path: str):
    if not data.folder_id:
        folder_name = f"File_NO-{uuid.uuid4().hex[:6]}"
        folder = Folder(
            name=folder_name,
            organization_id=data.organization_id,
            created_by_id=uploader_id,
        )
        db.add(folder)
        await db.flush()
        data.folder_id = folder.id
    doc = Document(
        file=file_path,
        uploader_id=uploader_id,
        **data.model_dump(),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


async def update_document(db: AsyncSession, doc_id: str, data: DocumentUpdate):
    doc = await get_document(db, doc_id)
    if not doc:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(doc, key, val)
    await db.commit()
    await db.refresh(doc)
    return doc


async def delete_document(db: AsyncSession, doc_id: str):
    doc = await get_document(db, doc_id)
    if not doc:
        return False
    await db.delete(doc)
    await db.commit()
    return True


async def get_folders(db: AsyncSession, organization_id: str, parent_id: str | None = None):
    stmt = select(Folder).where(Folder.organization_id == organization_id)
    if parent_id:
        stmt = stmt.where(Folder.parent_id == parent_id)
    else:
        stmt = stmt.where(Folder.parent_id.is_(None))
    result = await db.execute(stmt)
    return result.scalars().all()


async def create_folder(db: AsyncSession, data: FolderCreate, user_id: str):
    existing = await db.execute(
        select(Folder).where(
            and_(
                Folder.name == data.name,
                Folder.organization_id == data.organization_id,
                Folder.parent_id.is_(data.parent_id),
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A folder with this name already exists in this location")
    folder = Folder(created_by_id=user_id, **data.model_dump())
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    return folder


async def delete_folder(db: AsyncSession, folder_id: str):
    result = await db.execute(select(Folder).where(Folder.id == folder_id))
    folder = result.scalar_one_or_none()
    if not folder:
        return False
    await db.delete(folder)
    await db.commit()
    return True


async def search_documents(
    db: AsyncSession,
    query: str,
    organization_id: str,
    limit: int = 10,
    department_id: str | None = None,
    document_type_id: str | None = None,
    year: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    status: str | None = None,
    page: int = 1,
) -> list[SearchResultItem]:
    start = time.time()

    results = qdrant_search(query, organization_id, limit * 2)

    doc_ids = list(set(r["document_id"] for r in results))
    if not doc_ids:
        return []

    stmt = select(Document).options(
        joinedload(Document.department),
        joinedload(Document.document_type),
    ).where(Document.id.in_(doc_ids))

    if department_id:
        stmt = stmt.where(Document.department_id == department_id)
    if document_type_id:
        stmt = stmt.where(Document.document_type_id == document_type_id)
    if year:
        stmt = stmt.where(extract("year", Document.document_date) == year)
    if date_from:
        stmt = stmt.where(Document.document_date >= date_from)
    if date_to:
        stmt = stmt.where(Document.document_date <= date_to)
    if status:
        stmt = stmt.where(Document.status == status)

    doc_rows = await db.execute(stmt)
    filtered_docs = {d.id: d for d in doc_rows.unique().scalars().all()}

    items = []
    query_lower = query.lower()
    for r in results:
        doc = filtered_docs.get(r["document_id"])
        if not doc:
            continue
        content_lower = r["content"][:300].lower()
        # Determine match type: exact if query words appear in content
        query_words = [w for w in query_lower.split() if len(w) > 2]
        match_type = "exact" if any(w in content_lower for w in query_words) else "semantic"

        items.append(SearchResultItem(
            document_id=r["document_id"],
            document_subject=r.get("subject") or doc.subject,
            chunk_id=r["chunk_id"],
            content=r["content"][:300],
            score=r["score"],
            page_number=r.get("page_number"),
            match_type=match_type,
            department=doc.department.name if doc.department else None,
            document_type=doc.document_type.name if doc.document_type else None,
            file_number=doc.file_number,
            file_date=str(doc.document_date) if doc.document_date else None,
        ))

    offset = (page - 1) * limit
    return items[offset:offset + limit]


def get_departments(db: AsyncSession, organization_id: str):
    stmt = select(Department).where(Department.organization_id == organization_id)
    result = db.execute(stmt)
    return result.scalars().all()


def get_document_types(db: AsyncSession, organization_id: str):
    stmt = select(DocumentType).where(DocumentType.organization_id == organization_id)
    result = db.execute(stmt)
    return result.scalars().all()


def get_available_years(db: AsyncSession, organization_id: str):
    stmt = select(extract("year", Document.document_date)).where(
        Document.organization_id == organization_id,
        Document.document_date.isnot(None),
    ).distinct().order_by(extract("year", Document.document_date).desc())
    result = db.execute(stmt)
    return [r[0] for r in result if r[0]]
