from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.database.connection import Base


class DiscoveredItem(Base):
    __tablename__ = "discovered_items"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "source_type",
            "external_id",
            name="uq_user_source_item",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type = Column(String(50), nullable=False)  # "google_drive" or "github_repo"
    external_id = Column(String(255), nullable=False)  # Drive file id or repo full_name
    title = Column(String(255), nullable=False)
    subtitle = Column(String(100), nullable=True)  # "PDF", "DOCX", or repo language
    url = Column(String(500), nullable=True)
    is_relevant = Column(Boolean, default=False, nullable=False)
    is_selected = Column(Boolean, default=False, nullable=False)
    details = Column(JSON, nullable=False, default=dict)
    discovered_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

