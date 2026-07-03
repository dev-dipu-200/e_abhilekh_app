import json
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import get_db
from app.dependencies import get_current_user
from app.database.user_model import User
from app.module.file_manage.schema import (
    DraftGenerateRequest,
    DraftGenerateResponse,
    DraftCheckRequest,
    DraftCheckResponse,
    DraftSaveRequest,
    DraftExportRequest,
    DraftAttachRequest,
    SearchResultItem,
)
from app.database.file_model import Document
from app.module.draft_generation import service as draft_service
from app.utils.response import SuccessResponse

router = APIRouter(prefix="/draft", tags=["Draft Generation"])


@router.get("/templates")
async def list_templates():
    return SuccessResponse(result=draft_service.TEMPLATES, message="Templates retrieved", status_code=200)


@router.post("/generate/stream")
async def generate_draft_stream(
    data: DraftGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organization_id
    if not org_id:
        raise HTTPException(status_code=400, detail="User has no organization")

    if data.template_id == "information" and not data.instructions.strip():
        raise HTTPException(status_code=422, detail="Key Points/Instructions are required for Information template")

    context = await draft_service.build_draft_context(
        db=db,
        template_id=data.template_id,
        reference_id=data.reference_id,
        instructions=data.instructions,
        language=data.language,
        tone=data.tone,
        organization_id=org_id,
    )

    async def event_stream():
        draft_text = ""
        try:
            for chunk in draft_service.generate_draft_stream(context):
                draft_text += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'text': draft_text, 'subject': context.get('subject', '')})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/generate")
async def generate_draft(
    data: DraftGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organization_id
    if not org_id:
        raise HTTPException(status_code=400, detail="User has no organization")

    if data.template_id == "information" and not data.instructions.strip():
        raise HTTPException(status_code=422, detail="Key Points/Instructions are required for Information template")

    context = await draft_service.build_draft_context(
        db=db,
        template_id=data.template_id,
        reference_id=data.reference_id,
        instructions=data.instructions,
        language=data.language,
        tone=data.tone,
        organization_id=org_id,
    )

    raw_output = draft_service.generate_draft_non_stream(context)

    records = context.get("relevant_records", [])
    return SuccessResponse(
        result=DraftGenerateResponse(
            draft_text=raw_output,
            draft_html=raw_output,
            draft_json=json.dumps({"draft_text": raw_output, "subject": context.get("subject", "")}),
            relevant_records=records,
            subject=context.get("subject", ""),
            template_id=data.template_id,
            language=data.language,
            tone=data.tone,
        ),
        message="Draft generated",
        status_code=200,
    )


@router.post("/check")
async def check_draft(
    data: DraftCheckRequest,
    db: AsyncSession = Depends(get_db),
):
    draft = await draft_service.check_existing_draft(
        db=db,
        reference_id=data.reference_id,
        template_id=data.template_id,
        language=data.language,
        organization_id="",
    )
    if draft:
        return SuccessResponse(
            result=DraftCheckResponse(
                exists=True,
                draft_id=draft.id,
                draft=DraftGenerateResponse(
                    draft_text=draft.content_text or "",
                    draft_html=draft.content_html or "",
                    draft_json=draft.content_json or "",
                    template_id=draft.template_type,
                    language=draft.language,
                    tone=draft.tone or "formal",
                ),
            ),
            message="Existing draft found",
            status_code=200,
        )
    return SuccessResponse(
        result=DraftCheckResponse(exists=False),
        message="No existing draft found",
        status_code=200,
    )


@router.post("/save")
async def save_draft(
    data: DraftSaveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc_result = await db.execute(
        select(Document).where(Document.id == data.reference_id)
    )
    doc = doc_result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Reference document not found")

    draft = await draft_service.save_draft(
        db=db,
        reference_id=data.reference_id,
        template_id=data.template_id,
        language=data.language,
        tone=data.tone,
        subject=data.subject,
        instructions=data.instructions,
        draft_text=data.draft_text,
        draft_html=data.draft_html,
        draft_json=data.draft_json,
        document_id=doc.id,
    )
    return SuccessResponse(
        result={"id": draft.id, "template_type": draft.template_type},
        message="Draft saved successfully",
        status_code=200,
    )


@router.post("/export")
async def export_draft(
    data: DraftExportRequest,
    db: AsyncSession = Depends(get_db),
):
    content = await draft_service.export_draft(db, data.draft_id, data.format)
    if content is None:
        raise HTTPException(status_code=404, detail="Draft not found")

    from fastapi.responses import Response
    media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if data.format == "docx" else "text/plain"
    filename = f"draft_{data.draft_id}.{data.format}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/attach")
async def attach_draft(
    data: DraftAttachRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attachment = await draft_service.attach_draft_to_document(
        db=db,
        draft_id=data.draft_id,
        document_id=data.document_id,
        user_id=current_user.id,
    )
    if not attachment:
        raise HTTPException(status_code=404, detail="Draft or document not found")
    return SuccessResponse(
        result={"id": attachment.id, "filename": attachment.filename},
        message="Draft attached to document",
        status_code=200,
    )
