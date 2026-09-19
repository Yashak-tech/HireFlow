import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Text, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.resume import Resume
    from app.models.user import User


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    candidate_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    answer_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    claim_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    verbatim_source_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="resume", nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.00, nullable=False)
    is_overridden_by_human: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    overridden_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    override_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="evidence_items")
    resume: Mapped[Optional["Resume"]] = relationship("Resume", back_populates="evidence_items")
    overridden_by: Mapped[Optional["User"]] = relationship("User")
