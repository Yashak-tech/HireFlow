import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Text, Integer, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now

if TYPE_CHECKING:
    from app.models.interview import Interview
    from app.models.interview_answer import InterviewAnswer


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

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
        index=True,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # technical_depth, gap_probe, behavioral, culture_fit, situational
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str] = mapped_column(Text, nullable=False)
    targeted_gap: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rubric_criteria: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    is_customized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    interview: Mapped["Interview"] = relationship("Interview", back_populates="questions")
    answers: Mapped[List["InterviewAnswer"]] = relationship(
        "InterviewAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="InterviewAnswer.created_at",
        lazy="selectin",
    )
