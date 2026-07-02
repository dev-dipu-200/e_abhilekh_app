import io
import json
import uuid
import httpx
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.file_model import Document, GeneratedDraft, Attachment, ActivityLog
from app.utils.ollama_client import generate, chat
from app.utils.qdrant_store import search as qdrant_search
from app.settings.config import settings
from app.module.file_manage.schema import SearchResultItem

TEMPLATES = [
    {"id": "letter", "name": "Official Letter", "label": "letter", "description": "Draft a formal official letter", "icon": "file-text"},
    {"id": "circular", "name": "Circular", "label": "circular", "description": "Draft a department circular", "icon": "file-text"},
    {"id": "notice", "name": "Notice", "label": "notice", "description": "Draft a public or internal notice", "icon": "file-text"},
    {"id": "rti", "name": "RTI Reply", "label": "rti", "description": "Draft a reply to an RTI application", "icon": "file-text"},
    {"id": "information", "name": "Information", "label": "information", "description": "Draft an information memorandum", "icon": "file-text"},
]

SYSTEM_PROMPTS = {
    "letter": "You are a government letter drafting assistant. Draft formal official letters in the specified language and tone. Use proper government letter format with subject, reference, body, and signature block.",
    "circular": "You are a government circular drafting assistant. Draft department circulars in the specified language and tone. Include subject, preamble, instructions, and distribution list.",
    "notice": "You are a government notice drafting assistant. Draft public or internal notices in the specified language and tone. Include heading, date, body, and authority signature.",
    "rti": "You are an RTI reply drafting assistant. Draft replies to RTI applications in the specified language and tone. Include reference to the RTI application, point-wise responses, and appellate authority information.",
    "information": "You are an information memorandum drafting assistant. Draft information notes in the specified language and tone. Include subject, reference, detailed information, and conclusion.",
}

TEMPLATE_FORMATS = {
    "letter": {
        "format": "government_letter",
        "sections": ["subject", "reference", "preamble", "body", "conclusion", "signature"],
    },
    "circular": {
        "format": "government_circular",
        "sections": ["subject", "reference", "preamble", "instructions", "distribution"],
    },
    "notice": {
        "format": "government_notice",
        "sections": ["heading", "date", "body", "authority"],
    },
    "rti": {
        "format": "rti_reply",
        "sections": ["reference", "preliminary", "point_wise_responses", "appellate_info", "conclusion"],
    },
    "information": {
        "format": "information_memorandum",
        "sections": ["subject", "reference", "details", "conclusion"],
    },
}


async def get_document_with_relations(db: AsyncSession, doc_id: str):
    result = await db.execute(
        select(Document).options(
            joinedload(Document.department),
            joinedload(Document.document_type),
            joinedload(Document.folder),
        ).where(Document.id == doc_id)
    )
    return result.unique().scalar_one_or_none()


async def get_relevant_records(query: str, organization_id: str, limit: int = 5) -> list[SearchResultItem]:
    results = qdrant_search(query, organization_id, limit)
    return [
        SearchResultItem(
            document_id=r["document_id"],
            document_subject=r.get("subject"),
            chunk_id=r["chunk_id"],
            content=r["content"][:500],
            score=r["score"],
            page_number=r.get("page_number"),
            match_type="semantic",
        )
        for r in results
    ]


async def build_draft_context(
    db: AsyncSession,
    template_id: str,
    reference_id: str,
    instructions: str,
    language: str,
    tone: str,
    organization_id: str,
) -> dict:
    ref_doc = await get_document_with_relations(db, reference_id)
    ref_context = ""
    subject = ""
    if ref_doc:
        subject = ref_doc.subject or ""
        ref_context = (
            f"Reference Document: {ref_doc.file.split('/')[-1] if ref_doc.file else 'Unknown'}\n"
            f"Subject: {ref_doc.subject or 'N/A'}\n"
            f"Department: {ref_doc.department.name if ref_doc.department else 'N/A'}\n"
            f"Document Type: {ref_doc.document_type.name if ref_doc.document_type else 'N/A'}\n"
            f"File Number: {ref_doc.file_number or 'N/A'}\n"
        )

    relevant_records = await get_relevant_records(subject or reference_id, organization_id)
    records_text = ""
    if relevant_records:
        records_lines = []
        for r in relevant_records:
            records_lines.append(f"- {r.document_subject or 'Doc'}: {r.content[:200]}")
        records_text = "\n".join(records_lines)

    prompt_parts = [
        f"Draft Type: {template_id}",
        f"Language: {'Hindi' if language == 'hi' else 'English'}",
        f"Tone: {tone}",
        "",
        "=== REFERENCE DOCUMENT ===",
        ref_context,
    ]
    if records_text:
        prompt_parts.append("=== RELEVANT RECORDS ===")
        prompt_parts.append(records_text)
    if instructions:
        prompt_parts.append("=== USER INSTRUCTIONS ===")
        prompt_parts.append(instructions)

    prompt_parts.append(
        "\n=== OUTPUT FORMAT ===\n"
        "Return a structured JSON with these fields:\n"
        "{\n"
        '  "draft_text": "Full draft text in the specified language",\n'
        '  "subject": "Document subject",\n'
        '  "sections": {"section_name": "content"}\n'
        "}\n"
        "Write the draft in the exact language specified. "
        "If Hindi, use Devanagari script. "
        "Generate a fresh, original draft based on the reference document and instructions. "
        "Do not simply copy the source document."
    )

    return {
        "prompt": "\n".join(prompt_parts),
        "system_prompt": SYSTEM_PROMPTS.get(template_id, ""),
        "reference_document": ref_doc,
        "relevant_records": relevant_records,
        "subject": subject,
    }


def generate_draft_stream(context: dict):
    payload = {
        "model": settings.OLLAMA_GENERATION_MODEL,
        "prompt": context["prompt"],
        "system": context["system_prompt"],
        "stream": True,
        "options": {"temperature": 0.3},
    }
    with httpx.stream(
        "POST",
        f"{settings.OLLAMA_BASE_URL}/api/generate",
        json=payload,
        verify=False,
        timeout=300,
    ) as resp:
        for line in resp.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue


def generate_draft_non_stream(context: dict) -> str:
    return generate(
        prompt=context["prompt"],
        system=context["system_prompt"],
        temperature=0.3,
    )


def extract_draft_json(raw_text: str) -> dict:
    try:
        json_start = raw_text.index("{")
        json_end = raw_text.rindex("}") + 1
        return json.loads(raw_text[json_start:json_end])
    except (ValueError, json.JSONDecodeError):
        return {"draft_text": raw_text, "subject": "", "sections": {}}


async def check_existing_draft(
    db: AsyncSession,
    reference_id: str,
    template_id: str,
    language: str,
    organization_id: str,
):
    result = await db.execute(
        select(GeneratedDraft).where(
            GeneratedDraft.reference_document_id == reference_id,
            GeneratedDraft.template_type == template_id,
            GeneratedDraft.language == language,
        ).order_by(GeneratedDraft.created_at.desc())
    )
    return result.scalars().first()


async def save_draft(
    db: AsyncSession,
    reference_id: str,
    template_id: str,
    language: str,
    tone: str,
    subject: str,
    instructions: str,
    draft_text: str,
    draft_html: str,
    draft_json: str,
    document_id: str,
) -> GeneratedDraft:
    draft = GeneratedDraft(
        document_id=document_id,
        reference_document_id=reference_id,
        template_type=template_id,
        language=language,
        tone=tone,
        content_text=draft_text,
        content_html=draft_html,
        content_json=draft_json,
    )
    db.add(draft)
    await db.commit()
    await db.refresh(draft)
    return draft


async def export_draft(db: AsyncSession, draft_id: str, fmt: str) -> bytes | None:
    result = await db.execute(select(GeneratedDraft).where(GeneratedDraft.id == draft_id))
    draft = result.scalar_one_or_none()
    if not draft:
        return None

    text = draft.content_text or draft.content_html or ""

    if fmt == "txt":
        return text.encode("utf-8")

    try:
        from docx import Document as DocxDocument
        from docx.shared import Pt, Inches
        doc = DocxDocument()
        for line in text.split("\n"):
            if line.strip():
                p = doc.add_paragraph(line.strip())
                p.space_after = Pt(4)
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return buf.getvalue()
    except ImportError:
        return text.encode("utf-8")


async def attach_draft_to_document(
    db: AsyncSession,
    draft_id: str,
    document_id: str,
    user_id: str,
) -> Attachment | None:
    result = await db.execute(select(GeneratedDraft).where(GeneratedDraft.id == draft_id))
    draft = result.scalar_one_or_none()
    if not draft:
        return None

    doc_result = await db.execute(select(Document).where(Document.id == document_id))
    doc = doc_result.scalar_one_or_none()
    if not doc:
        return None

    filename = f"draft_{draft.template_type}_{uuid.uuid4().hex[:6]}.txt"
    attachment = Attachment(
        file=f"drafts/{doc.organization_id}/{filename}",
        filename=filename,
        document_id=document_id,
    )
    db.add(attachment)

    log = ActivityLog(
        document_id=document_id,
        action=f"Draft attached ({draft.template_type})",
        user_id=user_id,
        details=f"Draft {draft_id} attached as {filename}",
    )
    db.add(log)

    await db.commit()
    await db.refresh(attachment)
    return attachment
