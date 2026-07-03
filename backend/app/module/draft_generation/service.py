import io
import json
import uuid
import httpx
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text as sa_text
from app.database.file_model import Document, GeneratedDraft, Attachment, ActivityLog
from app.database.user_model import Organization, User
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

TEMPLATE_GUIDANCE = {
    "letter": "Use a classic official letter structure with recipient lines, a concise subject line that describes the administrative matter, formal salutation, two to four body paragraphs, and optional copy-to entries. Do not use a person's name as the subject unless the source explicitly makes that the subject.",
    "circular": "Draft this as a department circular. Keep a short opening, three to five clear numbered directives, and a short closure. Use formal administrative Hindi when language is hi.",
    "notice": "Draft this as a notice. Keep it concise, announcement-focused, and suitable for display on an office notice board. Use a clear notice title and avoid story-like paragraphs.",
    "rti": "Draft this as an RTI reply under the RTI Act, 2005. Use point-wise reply_items, answer the query directly, and mention the legal or procedural note in legal_note. Do not invent applicant details.",
    "information": "Draft this as an informative office document. Base the content on the analysed results from the key points/instructions, use a clear subject, a short context-setting opening, and well-structured factual paragraphs or bullet points. Keep it informative rather than directive.",
}

SYSTEM_PROMPTS = {
    "letter": """You are a government letter drafting assistant. Write a professional official letter in the specified language.

Use these EXACT labels: Header:, Subject:, Salutation:, Body:, Closure:, Signature:.

CRITICAL RULES:
1. NEVER use bracket placeholders like [Signature], [Name], [Date], [Designation], [Placeholder]. Fill in every field with concrete content based on the reference context provided.
2. The subject must describe the action/matter, not a person's name.
3. Write at least 200 words for the Body. Stop after the Signature section.
4. Do NOT wrap the draft in JSON. Just output the raw draft text with the labels above.
5. Do NOT use greetings like Namaste, Dear, etc.
6. No markdown, no code fences, no JSON markers.""",

    "circular": """You are a government circular drafting assistant. Draft a department circular in the specified language.

Use these EXACT labels: Header:, Subject:, Preamble:, Directives:, Closure:, Distribution:.

CRITICAL RULES:
1. NEVER use bracket placeholders. Fill every field with concrete content from the reference context.
2. Use 3 to 5 clear numbered directives in the Directives section.
3. Write at least 200 words total. Stop after Distribution.
4. Do NOT wrap the draft in JSON. Just output the raw draft text.
5. No markdown, no code fences, no JSON markers.""",

    "notice": """You are a government notice drafting assistant. Draft a public or internal notice in the specified language.

Use these EXACT labels: Notice Title:, Date:, Body:, Issued By:.

CRITICAL RULES:
1. NEVER use bracket placeholders. Fill every field with concrete content from the reference context.
2. Keep it concise and announcement-style. Avoid story-like paragraphs.
3. Stop after the Issued By section.
4. Do NOT wrap the draft in JSON. Just output the raw draft text.
5. No markdown, no code fences, no JSON markers.""",

    "rti": """You are an RTI reply drafting assistant under the RTI Act, 2005. Draft a reply to an RTI application in the specified language.

Use these EXACT labels: Reference:, Date:, From:, Subject:, Preliminary:, Point-wise Replies:, Legal Note:, Appeal Note:, Signatory:.

CRITICAL RULES:
1. NEVER use bracket placeholders. Fill every field with concrete content.
2. Answer point-wise and synthesize records entirely in the selected language.
3. Use DD/MM/YYYY date format.
4. Include first appeal details under Section 19(1).
5. Stop after the Signatory section.
6. Do NOT wrap the draft in JSON. Just output the raw draft text.
7. No markdown, no code fences, no JSON markers.""",

    "information": """You are an information memorandum drafting assistant. Draft an informative office document in the specified language.

Use these EXACT labels: Subject:, Reference:, Details:, Conclusion:.

CRITICAL RULES:
1. NEVER use bracket placeholders. Fill every field with concrete content from the reference context.
2. Base the content on the analysed results from key points/instructions.
3. Keep it informative rather than directive. Use bullet points where appropriate.
4. Stop after the Conclusion section.
5. Do NOT wrap the draft in JSON. Just output the raw draft text.
6. No markdown, no code fences, no JSON markers.""",
}

HINDI_LANGUAGE_RULES = """LANGUAGE RULES (Hindi mode):
- Every visible field MUST be in formal Hindi written in Devanagari script only.
- NO English in brackets. Do NOT write 'Hindi (English)'.
- Transliterate names and places into Devanagari (e.g., 'Imran' -> 'इमरान').
- Keep English ONLY for exact reference numbers (e.g., AUTO-123) and specific statute names.
- Translate all designations, departments, and body text into formal government Hindi.
- Use standard international/Latin numerals (0-9) for all numbers, years, and dates.
- Always format dates using hyphens (DD-MM-YYYY). NEVER use slashes.
- Never provide English translations in brackets. Use ONLY Devanagari Hindi.

TERMINOLOGY (Hindi):
- PWD = लोक निर्माण विभाग (NEVER use "पवित्र")
- Public Works Department = लोक निर्माण विभाग
- Office Order = कार्यालय आदेश
- Promotion = पदोन्नति
- Use professional Hindi words: पत्राचार, अनुपालन, निर्देश, पदोन्नति

Write in Hindi. Do not use greetings like नमस्ते or प्रिय."""

ENGLISH_LANGUAGE_RULES = """LANGUAGE RULES (English mode):
- Every visible field must be in professional English.
- Do not output any Devanagari characters anywhere in the visible draft.
- Reconstruct the draft from source facts and evidence items in professional English.
- If a source field is in Hindi script, rewrite it in English script or translate it.
- Always format dates using hyphens (DD-MM-YYYY) instead of slashes.
- Use professional formal English terminology.

Write in English. No greetings like Namaste or Dear."""

LANGUAGE_TERMINOLOGY = {
    "hi": HINDI_LANGUAGE_RULES,
    "en": ENGLISH_LANGUAGE_RULES,
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

    org_name = ""
    if organization_id:
        r = await db.execute(sa_text(f"SELECT name FROM organizations WHERE id = '{organization_id}'"))
        row = r.fetchone()
        if row:
            org_name = row[0]

    if ref_doc:
        subject = ref_doc.subject or ""
        designation = ref_doc.designation or ""
        file_number = ref_doc.file_number or ""
        dept_name = ref_doc.department.name if ref_doc.department else "N/A"
        doctype_name = ref_doc.document_type.name if ref_doc.document_type else "N/A"

        ref_context = (
            f"Reference Document: {ref_doc.file.split('/')[-1] if ref_doc.file else 'Unknown'}\n"
            f"Subject: {subject or 'N/A'}\n"
            f"Department: {dept_name}\n"
            f"Organization: {org_name}\n"
            f"Document Type: {doctype_name}\n"
            f"File Number: {file_number or 'N/A'}\n"
            f"Designation: {designation or 'N/A'}\n"
        )

    relevant_records = await get_relevant_records(subject or reference_id, organization_id)
    records_text = ""
    if relevant_records:
        records_lines = []
        for r in relevant_records:
            records_lines.append(f"- {r.document_subject or 'Doc'}: {r.content[:300]}")
        records_text = "\n".join(records_lines)

    visible_language = "Hindi" if language == "hi" else "English"
    template_name = next((t["name"] for t in TEMPLATES if t["id"] == template_id), template_id)

    prompt_parts = [
        f"Selected format: {template_name}",
        f"Target language: {visible_language}",
        f"Tone: {tone}",
        "",
        "=== REFERENCE DOCUMENT ===",
        ref_context,
    ]
    if records_text:
        prompt_parts.append("=== RELEVANT SEARCH RECORDS (from indexed documents) ===")
        prompt_parts.append(records_text)
    if instructions:
        prompt_parts.append("=== USER INSTRUCTIONS ===")
        prompt_parts.append(instructions)

    prompt_parts.append("")
    prompt_parts.append(f"=== TEMPLATE GUIDANCE ({template_name}) ===")
    prompt_parts.append(TEMPLATE_GUIDANCE.get(template_id, ""))

    prompt_parts.append("")
    prompt_parts.append("=== LANGUAGE RULES ===")
    prompt_parts.append(LANGUAGE_TERMINOLOGY.get(language, ENGLISH_LANGUAGE_RULES))

    prompt_parts.append("")
    prompt_parts.append("=== STRUCTURE LABELS ===")
    prompt_parts.append(
        "Use these EXACT labels in your output (one per line):\n"
        "Header:\n"
        "Subject:\n"
        "Salutation:\n"
        "Body:\n"
        "Closure:\n"
        "Signature:\n"
    )

    prompt_parts.append("")
    prompt_parts.append(
        "=== CRITICAL OUTPUT RULES ===\n"
        "1. NEVER use bracket placeholders like [Signature], [Name], [Date], [Designation], [Placeholder], [OM Number], etc. Fill in every field with concrete content from the reference context.\n"
        "2. If the reference context does not provide a specific value, infer it logically or leave it out entirely. Do NOT write placeholder brackets.\n"
        f"3. The subject must describe the action/matter, not a person's name.\n"
        f"4. Write at least 200 words for the body. Make the draft complete and actionable.\n"
        "5. Do NOT wrap the entire draft in JSON. Output raw text only, with the labels above.\n"
        "6. Do NOT use markdown, code fences, or any JSON delimiters.\n"
        "7. Do NOT include greetings like Namaste, Dear, प्रिय, नमस्ते.\n"
        "8. Base the draft primarily on the REFERENCE DOCUMENT. Use the search records as supporting evidence.\n"
        "9. Generate a fresh, original draft. Do not copy the reference document verbatim.\n"
        "10. Stop immediately after the Signature section."
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
