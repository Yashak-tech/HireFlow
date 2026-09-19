import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now, VectorEmbedding

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User
    from app.models.job_requirement import JobRequirement
    from app.models.candidate_match import CandidateMatch


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    org_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_by_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)
    raw_description: Mapped[str] = mapped_column(Text, nullable=False)
    optimized_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parsed_criteria: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    bias_risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bias_findings: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list, nullable=True)
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        VectorEmbedding,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="jobs")
    created_by: Mapped["User"] = relationship("User", back_populates="created_jobs")
    requirements: Mapped[List["JobRequirement"]] = relationship(
        "JobRequirement",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    matches: Mapped[List["CandidateMatch"]] = relationship(
        "CandidateMatch",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
