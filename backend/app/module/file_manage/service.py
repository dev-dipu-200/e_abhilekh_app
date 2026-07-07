import time
from fastapi import HTTPException
from sqlalchemy import select, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
import uuid
from app.database.file_model import Document, Folder, Department, DocumentType, ProcessingState, ActivityLog
from app.database.user_model import Organization, User
from app.module.file_manage.schema import DocumentCreate, DocumentUpdate, FolderCreate, SearchResultItem
from app.utils.ai_runtime import resolve_ai_config, resolve_org_ai_config
from app.utils.file_number import generate_file_number
from app.utils.pagination import paginate_select, paginate_sequence
from app.utils.qdrant_store import search as qdrant_search, delete_document_chunks


async def get_documents(
    db: AsyncSession,
    organization_id: str,
    folder_id: str | None = None,
    cursor: str | None = None,
    limit: int = 25,
):
    stmt = select(Document).options(
        joinedload(Document.department),
        joinedload(Document.document_type),
        joinedload(Document.organization),
    ).where(Document.organization_id == organization_id)
    if folder_id:
        stmt = stmt.where(Document.folder_id == folder_id)
    stmt = stmt.order_by(Document.created_at.desc(), Document.id.desc())
    return await paginate_select(db, stmt, cursor=cursor, limit=limit, unique=True)


async def get_document(db: AsyncSession, doc_id: str):
    result = await db.execute(
        select(Document).options(
            joinedload(Document.department),
            joinedload(Document.document_type),
            joinedload(Document.folder),
            joinedload(Document.organization),
        ).where(Document.id == doc_id)
    )
    return result.unique().scalar_one_or_none()


async def log_document_activity(
    db: AsyncSession,
    document_id: str,
    action: str,
    user_id: str | None = None,
    details: str | None = None,
):
    db.add(ActivityLog(
        document_id=document_id,
        action=action,
        user_id=user_id,
        details=details,
    ))


async def create_document(db: AsyncSession, data: DocumentCreate, uploader_id: str, file_path: str):
    if not data.file_number:
        data.file_number = await generate_file_number(db, data.organization_id)
    if not data.folder_id:
        folder_name = data.file_number
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
    await db.flush()
    await log_document_activity(
        db,
        document_id=doc.id,
        action="Document uploaded",
        user_id=uploader_id,
        details=f"{doc.subject or 'Untitled document'} uploaded using {doc.parser_type or 'pymupdf'} parser",
    )
    await db.commit()
    await db.refresh(doc)
    return doc


async def update_document(db: AsyncSession, doc_id: str, data: DocumentUpdate, user_id: str | None = None):
    doc = await get_document(db, doc_id)
    if not doc:
        return None
    changes = []
    for key, val in data.model_dump(exclude_unset=True).items():
        old_val = getattr(doc, key)
        setattr(doc, key, val)
        if old_val != val:
            changes.append(f"{key}: {old_val} -> {val}")
    if changes:
        await log_document_activity(
            db,
            document_id=doc.id,
            action="Document updated",
            user_id=user_id,
            details="; ".join(changes[:5]),
        )
    await db.commit()
    await db.refresh(doc)
    return doc


async def delete_document(db: AsyncSession, doc_id: str, user_id: str | None = None):
    doc = await get_document(db, doc_id)
    if not doc:
        return False
    org_result = await db.execute(select(Organization).where(Organization.id == doc.organization_id))
    organization = org_result.scalar_one_or_none()
    delete_document_chunks(doc.id, resolve_org_ai_config(organization, doc.organization_id))
    user_result = await db.execute(select(User).where(User.organization_id == doc.organization_id))
    for user in user_result.scalars().all():
        runtime = resolve_ai_config(organization, doc.organization_id, user)
        if runtime.scope_type == "user":
            delete_document_chunks(doc.id, runtime)
    await db.delete(doc)
    await db.commit()
    return True


async def get_folders(
    db: AsyncSession,
    organization_id: str,
    parent_id: str | None = None,
    cursor: str | None = None,
    limit: int = 25,
):
    stmt = select(Folder).where(Folder.organization_id == organization_id)
    if parent_id:
        stmt = stmt.where(Folder.parent_id == parent_id)
    else:
        stmt = stmt.where(Folder.parent_id.is_(None))
    stmt = stmt.order_by(Folder.created_at.desc(), Folder.id.desc())
    return await paginate_select(db, stmt, cursor=cursor, limit=limit)


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
    current_user: User | None = None,
    limit: int = 10,
    department_id: str | None = None,
    document_type_id: str | None = None,
    year: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    status: str | None = None,
    cursor: str | None = None,
):
    start = time.time()
    org_result = await db.execute(select(Organization).where(Organization.id == organization_id))
    organization = org_result.scalar_one_or_none()
    runtime = resolve_ai_config(organization, organization_id, current_user)

    # Pass metadata filters directly to Qdrant for pre-filtering accuracy
    results = qdrant_search(
        query,
        organization_id,
        runtime,
        limit * 3,
        department_id=department_id,
        document_type_id=document_type_id,
    )

    doc_ids = list(set(r["document_id"] for r in results))
    if not doc_ids:
        return []

    stmt = select(Document).options(
        joinedload(Document.department),
        joinedload(Document.document_type),
    ).where(Document.id.in_(doc_ids))

    # Secondary DB-level filters for year and date range
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
    query_words = [w for w in query_lower.split() if len(w) > 2]
    for r in results:
        doc = filtered_docs.get(r["document_id"])
        if not doc:
            continue
        content_snippet = r["content"][:600]
        content_lower = content_snippet.lower()
        # Exact match: all query words found verbatim in the content/subject
        subject_lower = (r.get("subject") or doc.subject or "").lower()
        exact_count = sum(1 for w in query_words if w in content_lower or w in subject_lower)
        match_type = "exact" if exact_count >= max(1, len(query_words) // 2) else "semantic"

        items.append(SearchResultItem(
            document_id=r["document_id"],
            document_subject=r.get("subject") or doc.subject,
            chunk_id=r["chunk_id"],
            content=content_snippet,
            score=r["score"],
            page_number=r.get("page_number"),
            match_type=match_type,
            department=doc.department.name if doc.department else None,
            document_type=doc.document_type.name if doc.document_type else None,
            file_number=doc.file_number,
            file_date=str(doc.document_date) if doc.document_date else None,
        ))

    return paginate_sequence(items, cursor=cursor, limit=limit)


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
