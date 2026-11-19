"""
SQLAlchemy model for storing tailored job application packages
(Resume and Cover Letter versions).
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.database.connection import Base


class GeneratedApplication(Base):
    """Stores generated resume and cover letter versions for a specific user and job."""

    __tablename__ = "generated_applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=True)

    # Structured document payloads (JSON)
    resume_data = Column(JSON, nullable=False)
    cover_letter_data = Column(JSON, nullable=False)

    version = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default="generated", nullable=False)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )