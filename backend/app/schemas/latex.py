"""
Pydantic schemas for LaTeX generation, editing, versioning, and compilation.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class TemplateItem(BaseModel):
    """Metadata describing a LaTeX document template."""

    id: str = Field(..., description="Template identifier (e.g. 'modern', 'classic', 'minimal').")
    name: str = Field(..., description="Human-readable template name.")
    description: str = Field(..., description="Description of formatting and aesthetic style.")
    category: str = Field(..., description="'resume' or 'cover_letter'.")


class TemplatesResponse(BaseModel):
    """List of available resume and cover letter LaTeX templates."""

    resume_templates: List[TemplateItem]
    cover_letter_templates: List[TemplateItem]


class RenderLatexRequest(BaseModel):
    """Request payload to render LaTeX source for an application."""

    application_id: int = Field(..., description="ID of the GeneratedApplication.")
    document_type: str = Field(default="resume", description="'resume' or 'cover_letter'.")
    template_name: str = Field(default="modern", description="Template key.")


class RenderLatexResponse(BaseModel):
    """Response containing rendered LaTeX source code."""

    application_id: int
    document_type: str
    template_name: str
    latex_code: str
    version_number: int


class ValidateLatexRequest(BaseModel):
    """Request payload to validate LaTeX source code syntax."""

    latex_code: str = Field(..., description="Raw LaTeX source code.")


class ValidateLatexResponse(BaseModel):
    """Validation response indicating syntax correctness and error detail."""

    is_valid: bool
    error_message: Optional[str] = None


class SaveVersionRequest(BaseModel):
    """Payload to save an edited or approved LaTeX version."""

    application_id: int
    document_type: str = Field(default="resume")
    template_name: str = Field(default="modern")
    latex_code: str
    is_approved: bool = Field(default=False)


class DocumentVersionItem(BaseModel):
    """Structured representation of a saved document version."""

    id: int
    application_id: int
    document_type: str
    template_name: str
    version_number: int
    latex_content: str
    is_approved: bool
    created_at: str


class CompileLatexRequest(BaseModel):
    """Payload to compile LaTeX source to PDF."""

    latex_code: str = Field(..., description="Raw LaTeX source code.")
    application_id: Optional[int] = Field(default=None)
    document_type: Optional[str] = Field(default="resume")


class DocumentVersionsResponse(BaseModel):
    """Response containing version history for an application."""

    versions: List[DocumentVersionItem]
