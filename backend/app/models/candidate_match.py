import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.candidate import Candidate


class CandidateMatch(Base):
    __tablename__ = "candidate_matches"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    overall_match_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, index=True)
    vector_similarity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    skill_overlap_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    experience_fit_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reasoning: Mapped[str] = mapped_column(Text, default="Pending evaluation", nullable=False)
    matched_skills: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    missing_skills: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    pipeline_stage: Mapped[str] = mapped_column(String(50), default="matched", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="matches")
    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="matches")
