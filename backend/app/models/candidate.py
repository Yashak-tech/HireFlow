import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.resume import Resume
    from app.models.candidate_skill import CandidateSkill
    from app.models.candidate_match import CandidateMatch
    from app.models.evidence import Evidence


class Candidate(Base):
    __tablename__ = "candidates"

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
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    current_title: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    current_company: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    years_of_experience: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parsed_profile: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="candidates")
    resumes: Mapped[List["Resume"]] = relationship(
        "Resume",
        back_populates="candidate",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    skills: Mapped[List["CandidateSkill"]] = relationship(
        "CandidateSkill",
        back_populates="candidate",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    matches: Mapped[List["CandidateMatch"]] = relationship(
        "CandidateMatch",
        back_populates="candidate",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    evidence_items: Mapped[List["Evidence"]] = relationship(
        "Evidence",
        back_populates="candidate",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
