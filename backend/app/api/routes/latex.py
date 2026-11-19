"""
LaTeX API Routes for CareerCraft AI.
Handles template discovery, Jinja2 rendering, syntax validation,
multi-version management, and PDF compilation with multi-user isolation.
"""
import io
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.guardrails.permissions import verify_application_ownership
from app.models.candidate_profile import CandidateProfile
from app.models.document_version import DocumentVersion
from app.models.generated_application import GeneratedApplication
from app.models.user import User
from app.schemas.latex import (
    CompileLatexRequest,
    DocumentVersionItem,
    DocumentVersionsResponse,
    RenderLatexRequest,
    RenderLatexResponse,
    SaveVersionRequest,
    TemplateItem,
    TemplatesResponse,
    ValidateLatexRequest,
    ValidateLatexResponse,
)
from app.services.latex_service import (
    COVER_LETTER_TEMPLATES,
    RESUME_TEMPLATES,
    compile_latex_to_pdf,
    render_cover_letter_latex,
    render_resume_latex,
    validate_latex_syntax,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/latex", tags=["LaTeX & Document Studio"])


@router.get("/templates", response_model=TemplatesResponse)
def list_templates(current_user: User = Depends(get_current_user)):
    """List all predefined deterministic resume and cover letter LaTeX templates."""
    resume_list = [
        TemplateItem(
            id=k,
            name=k.capitalize(),
            description=v,
            category="resume",
        )
        for k, v in RESUME_TEMPLATES.items()
    ]
    cover_letter_list = [
        TemplateItem(
            id=k,
            name=k.capitalize(),
            description=v,
            category="cover_letter",
        )
        for k, v in COVER_LETTER_TEMPLATES.items()
    ]
    return TemplatesResponse(
        resume_templates=resume_list,
        cover_letter_templates=cover_letter_list,
    )


@router.post("/validate", response_model=ValidateLatexResponse)
def validate_latex(
    payload: ValidateLatexRequest,
    current_user: User = Depends(get_current_user),
):
    """Validate LaTeX syntax, structure, matching environments, and security safety."""
    is_valid, err = validate_latex_syntax(payload.latex_code)
    return ValidateLatexResponse(is_valid=is_valid, error_message=err)


@router.post("/render", response_model=RenderLatexResponse)
def render_latex_document(
    payload: RenderLatexRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Render LaTeX source for an application using the specified template and document type."""
    # 1. Verify user ownership
    app_record = verify_application_ownership(payload.application_id, current_user.id, db)
    if not app_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {payload.application_id} not found or unauthorized.",
        )

    doc_type = payload.document_type.lower().strip()
    if doc_type not in ["resume", "cover_letter"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="document_type must be 'resume' or 'cover_letter'.",
        )

    template_name = payload.template_name.lower().strip()

    # 2. Check if an approved or saved version already exists for this template
    latest_version = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.application_id == app_record.id,
            DocumentVersion.user_id == current_user.id,
            DocumentVersion.document_type == doc_type,
            DocumentVersion.template_name == template_name,
        )
        .order_by(DocumentVersion.version_number.desc())
        .first()
    )

    if latest_version:
        return RenderLatexResponse(
            application_id=app_record.id,
            document_type=doc_type,
            template_name=template_name,
            latex_code=latest_version.latex_content,
            version_number=latest_version.version_number,
        )

    # 3. Otherwise render fresh LaTeX source
    try:
        if doc_type == "resume":
            resume_data = app_record.resume_data or {}
            latex_source = render_resume_latex(resume_data, template_name=template_name)
        else:
            cl_data = app_record.cover_letter_data or {}
            profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
            contact_info = {
                "full_name": profile.full_name if profile else current_user.full_name,
                "location": profile.headline if profile else None,
                "email": current_user.email,
            }
            latex_source = render_cover_letter_latex(cl_data, contact_info=contact_info, template_name=template_name)

        # 4. Save initial version record
        new_version = DocumentVersion(
            application_id=app_record.id,
            user_id=current_user.id,
            document_type=doc_type,
            template_name=template_name,
            version_number=1,
            latex_content=latex_source,
            is_approved=False,
        )
        db.add(new_version)
        db.commit()
        db.refresh(new_version)

        return RenderLatexResponse(
            application_id=app_record.id,
            document_type=doc_type,
            template_name=template_name,
            latex_code=latex_source,
            version_number=1,
        )

    except Exception as e:
        logger.error(f"Error rendering LaTeX: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LaTeX rendering error: {str(e)}",
        )


@router.post("/compile")
def compile_latex(
    payload: ValidateLatexRequest,
    current_user: User = Depends(get_current_user),
):
    """Compile LaTeX source code into a PDF binary stream."""
    is_valid, err = validate_latex_syntax(payload.latex_code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"LaTeX validation failed: {err}",
        )

    try:
        pdf_bytes = compile_latex_to_pdf(payload.latex_code)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'inline; filename="compiled_document.pdf"',
                "Content-Type": "application/pdf",
            },
        )
    except Exception as e:
        logger.error(f"Compilation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF compilation failed: {str(e)}",
        )


@router.post("/save-version", response_model=DocumentVersionItem)
def save_document_version(
    payload: SaveVersionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save an edited or approved LaTeX version to preserve document version history."""
    app_record = verify_application_ownership(payload.application_id, current_user.id, db)
    if not app_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found or unauthorized.",
        )

    is_valid, err = validate_latex_syntax(payload.latex_code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot save invalid LaTeX: {err}",
        )

    # Determine next version number
    current_max = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.application_id == app_record.id,
            DocumentVersion.user_id == current_user.id,
            DocumentVersion.document_type == payload.document_type,
        )
        .order_by(DocumentVersion.version_number.desc())
        .first()
    )
    next_version = (current_max.version_number + 1) if current_max else 1

    version_record = DocumentVersion(
        application_id=app_record.id,
        user_id=current_user.id,
        document_type=payload.document_type,
        template_name=payload.template_name,
        version_number=next_version,
        latex_content=payload.latex_code,
        is_approved=payload.is_approved,
    )
    db.add(version_record)

    if payload.is_approved:
        db.query(GeneratedApplication).filter(GeneratedApplication.id == app_record.id).update(
            {"status": "finalized"}
        )

    db.commit()
    db.refresh(version_record)

    return DocumentVersionItem(
        id=version_record.id,
        application_id=version_record.application_id,
        document_type=version_record.document_type,
        template_name=version_record.template_name,
        version_number=version_record.version_number,
        latex_content=version_record.latex_content,
        is_approved=version_record.is_approved,
        created_at=version_record.created_at.isoformat() if version_record.created_at else "",
    )


@router.get("/versions/{application_id}", response_model=DocumentVersionsResponse)
def get_document_versions(
    application_id: int,
    document_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve the full version history of generated and edited LaTeX documents for an application."""
    app_record = verify_application_ownership(application_id, current_user.id, db)
    if not app_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found or unauthorized.",
        )

    query = db.query(DocumentVersion).filter(
        DocumentVersion.application_id == application_id,
        DocumentVersion.user_id == current_user.id,
    )
    if document_type:
        query = query.filter(DocumentVersion.document_type == document_type)

    records = query.order_by(DocumentVersion.version_number.desc()).all()

    items = [
        DocumentVersionItem(
            id=r.id,
            application_id=r.application_id,
            document_type=r.document_type,
            template_name=r.template_name,
            version_number=r.version_number,
            latex_content=r.latex_content,
            is_approved=r.is_approved,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in records
    ]
    return DocumentVersionsResponse(versions=items)


@router.get("/download/{version_id}")
def download_document_version(
    version_id: int,
    format: str = Query("pdf", pattern="^(pdf|tex)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download an approved or saved version as a raw .tex source file or compiled .pdf."""
    version_record = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.id == version_id,
            DocumentVersion.user_id == current_user.id,
        )
        .first()
    )
    if not version_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version record not found or unauthorized.",
        )

    filename_base = f"{version_record.document_type}_v{version_record.version_number}"

    if format == "tex":
        return Response(
            content=version_record.latex_content,
            media_type="text/x-tex",
            headers={
                "Content-Disposition": f'attachment; filename="{filename_base}.tex"',
            },
        )

    # Compile to PDF
    pdf_bytes = compile_latex_to_pdf(version_record.latex_content)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename_base}.pdf"',
        },
    )
