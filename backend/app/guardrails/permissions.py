"""
Permissions and Multi-Tenant Access Control Guardrail.
Ensures authenticated users can only query, revise, or export their own application records.
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.generated_application import GeneratedApplication


def verify_application_ownership(
    application_id: int,
    user_id: int,
    db: Session,
) -> Optional[GeneratedApplication]:
    """Verify that the requested application belongs to the authenticated user.

    Args:
        application_id: ID of the GeneratedApplication record.
        user_id: ID of the currently authenticated User.
        db: Active SQLAlchemy database session.

    Returns:
        GeneratedApplication record if owned by user; None if not found or unauthorized.
    """
    return (
        db.query(GeneratedApplication)
        .filter(
            GeneratedApplication.id == application_id,
            GeneratedApplication.user_id == user_id,
        )
        .first()
    )