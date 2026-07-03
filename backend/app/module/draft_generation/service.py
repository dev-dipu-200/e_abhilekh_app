import io
import json
import uuid
import httpx
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text as sa_text
from app.database.file_model import Document, DocumentChunk, GeneratedDraft, Attachment, ActivityLog
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

Use EXACTLY these labels with content on the SAME line after the colon:
  Header: <content>
  Subject: <content>
  Salutation: <content>
  Body: (newline then paragraphs)
  Closure: <content>
  Signature: <content>

For Body: put the content on the NEXT line (newline after the label), then write paragraphs.
For all OTHER labels: put content immediately on the same line after the colon and space.
Never insert blank lines between a label and its content.

CRITICAL RULES:
1. NEVER use bracket placeholders like [Signature], [Name], [Date], [Designation], [Placeholder]. Fill in every field with concrete content based on the reference context provided.
2. The subject must describe the action/matter, not a person's name.
3. Write at least 200 words for the Body. Stop after the Signature section.
4. Do NOT wrap the draft in JSON. Just output the raw draft text with the labels above.
5. Do NOT use greetings like Namaste, Dear, etc.
6. No markdown, no code fences, no JSON markers.""",

    "circular": """You are a government circular drafting assistant. Draft a department circular in the specified language.

Use EXACTLY these labels with content on the SAME line after the colon:
  Header: <content>
  Subject: <content>
  Preamble: <content>
  Directives: (newline then numbered items)
  Closure: <content>
  Distribution: <content>

For Directives: put content on the NEXT line, then write 3-5 numbered items.
For all OTHER labels: put content on same line after the colon.
No blank lines between a label and its content.

CRITICAL RULES:
1. NEVER use bracket placeholders. Fill every field with concrete content from the reference context.
2. Use 3 to 5 clear numbered directives in the Directives section.
3. Write at least 200 words total. Stop after Distribution.
4. Do NOT wrap the draft in JSON. Just output the raw draft text.
5. No markdown, no code fences, no JSON markers.""",

    "notice": """You are a government notice drafting assistant. Draft a public or internal notice in the specified language.

Use EXACTLY these labels with content on the SAME line after the colon:
  Notice Title: <content>
  Date: <content>
  Body: (newline then paragraphs)
  Issued By: <content>

For Body: put content on the NEXT line.
For all other labels: content on same line. No blank lines between label and content.

CRITICAL RULES:
1. NEVER use bracket placeholders. Fill every field with concrete content from the reference context.
2. Keep it concise and announcement-style. Avoid story-like paragraphs.
3. Stop after the Issued By section.
4. Do NOT wrap the draft in JSON. Just output the raw draft text.
5. No markdown, no code fences, no JSON markers.""",

    "rti": """You are an RTI reply drafting assistant under the RTI Act, 2005. Draft a reply to an RTI application in the specified language.

Use EXACTLY these labels with content on the SAME line after the colon:
  Reference: <content>
  Date: <content>
  From: <content>
  Subject: <content>
  Preliminary: <content>
  Point-wise Replies: (newline then numbered replies)
  Legal Note: <content>
  Appeal Note: <content>
  Signatory: <content>

For Point-wise Replies: put content on the NEXT line.
For all other labels: content on same line. No blank lines between label and content.

CRITICAL RULES:
1. NEVER use bracket placeholders. Fill every field with concrete content.
2. Answer point-wise and synthesize records entirely in the selected language.
3. Use DD/MM/YYYY date format.
4. Include first appeal details under Section 19(1).
5. Stop after the Signatory section.
6. Do NOT wrap the draft in JSON. Just output the raw draft text.
7. No markdown, no code fences, no JSON markers.""",

    "information": """You are an information memorandum drafting assistant. Draft an informative office document in the specified language.

Use EXACTLY these labels with content on the SAME line after the colon:
  Subject: <content>
  Reference: <content>
  Details: (newline then content)
  Conclusion: <content>

For Details: put content on the NEXT line.
For all other labels: content on same line. No blank lines between label and content.

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


async def get_document_full_text(db: AsyncSession, doc_id: str, max_chars: int = 3000) -> str:
    """Fetch the full extracted text from DocumentChunk records for richer LLM context."""
    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == doc_id)
        .order_by(DocumentChunk.chunk_index)
    )
    chunks = result.scalars().all()
    if not chunks:
        return ""
    # Join all chunks, truncate to max_chars to stay within LLM context
    full_text = "\n\n".join(c.content for c in chunks)
    return full_text[:max_chars]

async def get_relevant_records(
    query: str,
    organization_id: str,
    limit: int = 8,
    secondary_query: str = "",
) -> list[SearchResultItem]:
    """Retrieve semantically relevant records for draft context.
    
    Uses query expansion: runs primary + secondary queries and deduplicates,
    which broadens recall for more complete draft grounding.
    """
    results = qdrant_search(query, organization_id, limit)

    # Query expansion: also search using secondary_query (e.g., user instructions)
    if secondary_query and secondary_query.strip() and secondary_query != query:
        secondary = qdrant_search(secondary_query.strip(), organization_id, limit // 2)
        seen_chunk_ids = {r["chunk_id"] for r in results}
        for r in secondary:
            if r["chunk_id"] not in seen_chunk_ids:
                results.append(r)
                seen_chunk_ids.add(r["chunk_id"])

    return [
        SearchResultItem(
            document_id=r["document_id"],
            document_subject=r.get("subject"),
            chunk_id=r["chunk_id"],
            content=r["content"][:600],  # More context per snippet
            score=r["score"],
            page_number=r.get("page_number"),
            match_type="semantic",
        )
        for r in results[:limit]
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

    # Fetch full extracted text for richer LLM grounding
    ref_full_text = ""
    if ref_doc:
        ref_full_text = await get_document_full_text(db, reference_id, max_chars=3000)

    # Use query expansion: combine subject + user instructions for broader relevant record retrieval
    relevant_records = await get_relevant_records(
        subject or reference_id,
        organization_id,
        secondary_query=instructions,
    )
    records_text = ""
    if relevant_records:
        records_lines = []
        for r in relevant_records:
            records_lines.append(f"- {r.document_subject or 'Doc'}: {r.content[:500]}")
        records_text = "\n".join(records_lines)

    visible_language = "Hindi" if language == "hi" else "English"
    template_name = next((t["name"] for t in TEMPLATES if t["id"] == template_id), template_id)

    prompt_parts = [
        f"Selected format: {template_name}",
        f"Target language: {visible_language}",
        f"Tone: {tone}",
        "",
        "=== REFERENCE DOCUMENT METADATA ===",
        ref_context,
    ]

    # Include full extracted text for maximum factual grounding
    if ref_full_text:
        prompt_parts.append("=== REFERENCE DOCUMENT EXTRACTED TEXT (use this as primary content source) ===")
        prompt_parts.append(ref_full_text)

    if records_text:
        prompt_parts.append("=== RELEVANT SUPPORTING RECORDS (from other indexed documents) ===")
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

    STRUCTURE_LABELS_MAP = {
        "letter": {
            "labels": ["Header: <text>", "Subject: <text>", "Salutation: <text>", "Body: <paragraphs>", "Closure: <text>", "Signature: <text>"],
            "multiline": ["Body"],
            "example_correct": "Header: सरकारी पत्र\nSubject: उत्तर प्रदेश सरकार के अधीनस्थ विभागों में पदोन्नति नीति\nSalutation: पूर्ववर्ती, शासन\nBody:\nयह पत्र आपको सूचित करने के लिए है कि...\n\nइस नीति के तहत...\nClosure: यह पत्र सरकारी उद्देश्यों के लिए जारी किया गया है।\nSignature: (अधिकारी का नाम), (पदनाम)",
            "example_wrong": "Header:\n\nसरकारी पत्र\n\n\nSubject:\nsome text\n\nDo NOT output like the wrong example above.",
        },
        "circular": {
            "labels": ["Header: <text>", "Subject: <text>", "Preamble: <text>", "Directives: <numbered items>", "Closure: <text>", "Distribution: <text>"],
            "multiline": ["Directives"],
            "example_correct": "Header: शासनादेश\nSubject: विभागीय परिपत्र\nPreamble: सभी अधीनस्थ कार्यालयों को निर्देशित किया जाता है...\nDirectives:\n1. नीति का अनुपालन सुनिश्चित करें\n2. रिपोर्ट 31 अगस्त तक प्रस्तुत करें\nClosure: यह परिपत्र सभी संबंधित अधिकारियों को निर्देशित है।\nDistribution: सभी जिलाधिकारी, उत्तर प्रदेश",
            "example_wrong": "",
        },
        "notice": {
            "labels": ["Notice Title: <text>", "Date: <text>", "Body: <paragraphs>", "Issued By: <text>"],
            "multiline": ["Body"],
            "example_correct": "Notice Title: सार्वजनिक सूचना\nDate: 05-05-2026\nBody:\nसूचना के माध्यम से सभी संबंधितों को अवगत कराया जाता है...\nIssued By: जिला मजिस्ट्रेट, लखनऊ",
            "example_wrong": "",
        },
        "rti": {
            "labels": ["Reference: <text>", "Date: <text>", "From: <text>", "Subject: <text>", "Preliminary: <text>", "Point-wise Replies: <numbered replies>", "Legal Note: <text>", "Appeal Note: <text>", "Signatory: <text>"],
            "multiline": ["Point-wise Replies"],
            "example_correct": "Reference: RTI आवेदन संख्या RTI/2026/123\nDate: 05-05-2026\nFrom: सार्वजनिक सूचना अधिकारी\nSubject: सूचना का अधिकार अधिनियम, 2005 के तहत उत्तर\nPreliminary: प्रस्तुत प्रकरण में...\nPoint-wise Replies:\n1. प्रश्न 1 का उत्तर: ...\n2. प्रश्न 2 का उत्तर: ...\nLegal Note: धारा 8(1) के तहत छूट...\nAppeal Note: प्रथम अपील धारा 19(1) के तहत...\nSignatory: (नाम), सार्वजनिक सूचना अधिकारी",
            "example_wrong": "",
        },
        "information": {
            "labels": ["Subject: <text>", "Reference: <text>", "Details: <content>", "Conclusion: <text>"],
            "multiline": ["Details"],
            "example_correct": "Subject: विभागीय जानकारी\nReference: पत्र संख्या 3/2026/268\nDetails:\nप्रस्तुत प्रकरण में विभाग द्वारा...\n\nइसके अतिरिक्त...\nConclusion: उपरोक्त जानकारी आपके संदर्भ हेतु प्रस्तुत है।",
            "example_wrong": "",
        },
    }

    struct = STRUCTURE_LABELS_MAP.get(template_id, STRUCTURE_LABELS_MAP["letter"])
    labels_text = "\n".join(struct["labels"])
    multiline_str = ", ".join(struct["multiline"])
    multiline_names = " or ".join(struct["multiline"])

    prompt_parts.append(
        f"Use these EXACT labels followed by a colon and a space, then the content on the SAME line:\n"
        f"{labels_text}\n"
        f"\n"
        f"Only the {multiline_str} label(s) get a newline after it (to separate paragraphs/items).\n"
        f"All other labels: content follows on the SAME line after 'Label: '.\n"
        f"Never put a blank line between a label and its content."
    )

    prompt_parts.append("")
    example_correct = struct.get("example_correct")
    example_wrong = struct.get("example_wrong")
    if example_correct:
        ex = f"=== FORMATTING EXAMPLE (correct) ===\n{example_correct}"
        if example_wrong:
            ex += f"\n\n=== FORMATTING EXAMPLE (wrong) ===\n{example_wrong}"
        else:
            ex += "\n\nEnsure all non-body labels have content on the same line as the label."
        prompt_parts.append(ex)

    prompt_parts.append("")
    prompt_parts.append(
        "=== CRITICAL OUTPUT RULES ===\n"
        "1. NEVER use bracket placeholders like [Signature], [Name], [Date], [Designation], [Placeholder], [OM Number], etc. Fill in every field with concrete content from the reference context.\n"
        "2. If the reference context does not provide a specific value, infer it logically or leave it out entirely. Do NOT write placeholder brackets.\n"
        f"3. The subject must describe the action/matter, not a person's name.\n"
        f"4. Write a MINIMUM of 150 words. The draft must be complete, detailed, and actionable. Short drafts are unacceptable.\n"
        "5. Every claim in the draft must be grounded in the REFERENCE DOCUMENT or the RELEVANT SEARCH RECORDS provided above. Do not invent facts.\n"
        "6. Do NOT wrap the entire draft in JSON. Output raw text only, with the labels above.\n"
        "7. Do NOT use markdown, code fences, or any JSON delimiters.\n"
        "8. Do NOT include greetings like Namaste, Dear, प्रिय, नमस्ते.\n"
        "9. Base the draft primarily on the REFERENCE DOCUMENT. Use the search records as supporting evidence.\n"
        "10. Generate a fresh, original draft. Do not copy the reference document verbatim.\n"
        "11. Stop immediately after the final section.\n"
        "12. NO blank lines between a label colon and its content. Content goes on the same line as the label."
    )

    if template_id == "information":
        prompt_parts.append("")
        prompt_parts.append(
            "=== USER KEY POINTS / INSTRUCTIONS ===\n"
            f"The user has provided the following key points and instructions above (under 'USER INSTRUCTIONS'). "
            f"These are the PRIMARY source of content for this Information document. "
            f"Analyse each key point thoroughly and expand it into well-structured paragraphs. "
            f"Use the REFERENCE DOCUMENT and SEARCH RECORDS only as supporting context. "
            f"Do not deviate from the user's key points."
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
        "messages": [
            {"role": "system", "content": context["system_prompt"]},
            {"role": "user", "content": context["prompt"]},
        ],
        "stream": True,
        "options": {
            "temperature": 0.5,
            "num_predict": 2048,
            "repeat_penalty": 1.1,
        },
    }
    with httpx.stream(
        "POST",
        f"{settings.OLLAMA_BASE_URL}/api/chat",
        json=payload,
        verify=False,
        timeout=300,
    ) as resp:
        for line in resp.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    # /api/chat streaming returns message.content
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue


def generate_draft_non_stream(context: dict) -> str:
    return chat(
        messages=[
            {"role": "system", "content": context["system_prompt"]},
            {"role": "user", "content": context["prompt"]},
        ],
        temperature=0.5,
        num_predict=2048,
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
