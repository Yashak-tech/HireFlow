import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now

if TYPE_CHECKING:
    from app.models.interview import Interview
    from app.models.candidate_match import CandidateMatch
    from app.models.user import User


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    interview_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("interviews.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    match_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("candidate_matches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    technical_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    communication_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    depth_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    overall_interview_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, index=True)
    category_scores: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    strengths: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    weaknesses: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    ai_recommendation: Mapped[str] = mapped_column(
        String(50),
        default="review_needed",
        nullable=False,
        index=True,
    )  # advance, review_needed, reject
    human_decision: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )  # advanced, rejected, follow_up
    human_decision_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    human_decision_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    human_decision_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationships
    interview: Mapped["Interview"] = relationship("Interview", back_populates="evaluation")
    match: Mapped[Optional["CandidateMatch"]] = relationship("CandidateMatch")
    human_decision_by: Mapped[Optional["User"]] = relationship("User")
