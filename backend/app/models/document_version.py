"""
SQLAlchemy model for storing versions of rendered LaTeX documents (Resumes and Cover Letters).
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database.connection import Base


class DocumentVersion(Base):
    """Stores versioned LaTeX source code and approval status for generated applications."""

    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(
        Integer,
        ForeignKey("generated_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type = Column(String(50), nullable=False)  # "resume" or "cover_letter"
    template_name = Column(String(50), default="modern", nullable=False)
    version_number = Column(Integer, default=1, nullable=False)
    latex_content = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
