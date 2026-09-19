from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RequirementMatchItem(BaseModel):
    """Evaluation breakdown for an individual job requirement against candidate evidence."""
    requirement_id: Optional[str] = None
    requirement_text: str
    requirement_type: str = Field(default="must_have", description="'must_have' or 'nice_to_have'")
    category: str = Field(default="skill", description="'skill', 'experience', or 'domain'")
    weight: float = 1.0
    status: str = Field(description="'MATCHED', 'MISSING', or 'UNCLEAR'")
    evidence_quote: Optional[str] = Field(
        default=None,
        description="Verbatim excerpt from candidate resume or 'No explicit experience found in candidate evidence'",
    )
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)


class CandidateMatchCard(BaseModel):
    """Ranked match scorecard for a candidate against a job requisition."""
    match_id: str
    job_id: str
    candidate_id: str
    candidate_name: str
    candidate_email: str
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    years_of_experience: Optional[float] = None
    overall_match_score: float = Field(ge=0.0, le=100.0)
    vector_similarity: float = Field(ge=0.0, le=1.0)
    skill_overlap_score: float = Field(ge=0.0, le=100.0)
    experience_fit_score: float = Field(ge=0.0, le=100.0)
    pipeline_stage: str
    reasoning: str
    matched_skills: List[Dict[str, Any]] = Field(default_factory=list)
    missing_skills: List[Dict[str, Any]] = Field(default_factory=list)
    requirements_breakdown: List[RequirementMatchItem] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class MatchRunResponse(BaseModel):
    """Response returned upon running the Two-Stage Candidate Matching Engine."""
    job_id: str
    job_title: str
    total_candidates_evaluated: int
    matches: List[CandidateMatchCard]
    run_at: datetime
