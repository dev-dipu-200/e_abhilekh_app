import os
from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.settings.config import settings
from app.database.user_model import Organization
from app.database.file_model import Document, DocumentChunk, ProcessingState
from app.module.file_manage.parsers import parse_document
from app.utils.embeddings import encode_documents
from app.utils.qdrant_store import upsert_chunks, delete_document_chunks

celery_app = Celery(__name__, broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)

_sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
_sync_engine = create_engine(_sync_url, pool_pre_ping=True)
_SyncSession = sessionmaker(bind=_sync_engine)


def _get_doc(session: Session, doc_id: str) -> Document | None:
    return session.query(Document).filter(Document.id == doc_id).first()


def _chunk_text(text: str, max_chars: int = 384) -> list[tuple[str, int]]:
    paragraphs = text.split("\n\n")
    chunks: list[tuple[str, int]] = []
    current = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) < max_chars:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append((current, 0))
            while len(para) > max_chars:
                chunks.append((para[:max_chars], 0))
                para = para[max_chars:]
            current = para
    if current:
        chunks.append((current, 0))
    if not chunks:
        chunks.append((text[:max_chars], 0))
    return chunks


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_document_file(self, document_id: str):
    session = _SyncSession()
    try:
        doc = _get_doc(session, document_id)
        if not doc:
            return {"error": "Document not found", "id": document_id}

        doc.processing_state = ProcessingState.IN_PROGRESS
        session.commit()

        result = parse_document(doc.file, doc.parser_type)

        doc.subject = result.get("subject")
        doc.processing_state = ProcessingState.DONE
        session.commit()

        raw_text = result.get("raw_text") or ""
        pages = result.get("pages") or []
        if raw_text.strip():
            try:
                chunk_texts = []
                qdrant_chunks = []
                chunk_index = 0
                for page_num, page_text in enumerate(pages):
                    if not page_text.strip():
                        continue
                    page_chunks = _chunk_text(page_text)
                    for chunk_text, _ in page_chunks:
                        chunk = DocumentChunk(
                            document_id=document_id,
                            content=chunk_text,
                            chunk_index=chunk_index,
                            page_number=page_num + 1,
                        )
                        session.add(chunk)
                        session.flush()
                        chunk_texts.append(chunk_text)
                        qdrant_chunks.append({
                            "id": chunk.id,
                            "chunk_id": chunk.id,
                            "content": chunk_text,
                            "page_number": page_num + 1,
                            "subject": doc.subject,
                            "organization_id": doc.organization_id,
                            "document_id": document_id,
                        })
                        chunk_index += 1

                if chunk_texts:
                    embeddings = encode_documents(chunk_texts)
                    for qc, emb in zip(qdrant_chunks, embeddings):
                        qc["vector"] = emb
                    upsert_chunks(qdrant_chunks)
                session.commit()
            except Exception:
                import traceback
                traceback.print_exc()

        return {
            "id": document_id,
            "page_count": result.get("page_count"),
            "subject": result.get("subject"),
            "processing_state": "DONE",
        }

    except Exception as exc:
        session.rollback()
        try:
            doc = _get_doc(session, document_id)
            if doc:
                doc.processing_state = ProcessingState.FAILED
                session.commit()
        except Exception:
            pass
        raise self.retry(exc=exc)

    finally:
        session.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def generate_document_preview(self, document_id: str):
    session = _SyncSession()
    try:
        doc = _get_doc(session, document_id)
        if not doc:
            return {"error": "Document not found", "id": document_id}

        file_path = doc.file
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        preview_dir = f"previews/{doc.organization_id}/"
        os.makedirs(preview_dir, exist_ok=True)

        import fitz
        pdf = fitz.open(file_path)
        page_count = min(pdf.page_count, 5)
        for i in range(page_count):
            page = pdf.load_page(i)
            pix = page.get_pixmap(dpi=72)
            pix.save(os.path.join(preview_dir, f"{document_id}_page_{i+1}.png"))
        pdf.close()

        return {"id": document_id, "preview_count": page_count}

    except Exception as exc:
        raise self.retry(exc=exc)

    finally:
        session.close()
