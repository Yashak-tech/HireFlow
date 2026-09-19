from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class EvidenceBase(BaseModel):
    claim_type: str = Field(..., max_length=50, description="Category of claim: skill, experience, education, project, certification")
    claim_text: str = Field(..., min_length=1, description="The specific assertion or entity extracted")
    verbatim_source_text: str = Field(..., min_length=1, description="Exact quotation from source document proving the claim")
    source_type: str = Field(default="resume", max_length=50)
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)


class EvidenceCreate(EvidenceBase):
    candidate_id: str
    resume_id: Optional[str] = None
    answer_id: Optional[str] = None


class EvidenceOverride(BaseModel):
    is_overridden_by_human: bool = True
    override_reason: str = Field(..., min_length=2)


class EvidenceResponse(EvidenceBase):
    id: str
    candidate_id: str
    resume_id: Optional[str] = None
    answer_id: Optional[str] = None
    is_overridden_by_human: bool = False
    overridden_by_user_id: Optional[str] = None
    override_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
