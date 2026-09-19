import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Text, Integer, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.candidate import Candidate
    from app.models.candidate_match import CandidateMatch
    from app.models.user import User
    from app.models.interview_question import InterviewQuestion
    from app.models.interview_answer import InterviewAnswer
    from app.models.evaluation import Evaluation


class Interview(Base):
    __tablename__ = "interviews"

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
    match_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("candidate_matches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="scheduled",
        nullable=False,
        index=True,
    )  # scheduled, in_progress, completed, cancelled, aborted
    current_question_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tamper_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    tamper_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationships
    job: Mapped["Job"] = relationship("Job", lazy="selectin")
    candidate: Mapped["Candidate"] = relationship("Candidate", lazy="selectin")
    match: Mapped[Optional["CandidateMatch"]] = relationship("CandidateMatch", lazy="selectin")
    created_by: Mapped["User"] = relationship("User", lazy="selectin")
    questions: Mapped[List["InterviewQuestion"]] = relationship(
        "InterviewQuestion",
        back_populates="interview",
        cascade="all, delete-orphan",
        order_by="InterviewQuestion.order_index",
        lazy="selectin",
    )
    answers: Mapped[List["InterviewAnswer"]] = relationship(
        "InterviewAnswer",
        back_populates="interview",
        cascade="all, delete-orphan",
        order_by="InterviewAnswer.created_at",
        lazy="selectin",
    )
    evaluation: Mapped[Optional["Evaluation"]] = relationship(
        "Evaluation",
        back_populates="interview",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
