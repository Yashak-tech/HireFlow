from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict

JobStatus = Literal["draft", "active", "paused", "closed"]
RequirementType = Literal["must_have", "nice_to_have", "preferred"]
RequirementCategory = Literal["skill", "experience", "education", "domain"]


class JobRequirementBase(BaseModel):
    requirement_text: str = Field(..., min_length=2, max_length=1000)
    requirement_type: RequirementType = "must_have"
    category: RequirementCategory = "skill"
    weight: float = Field(default=1.0, ge=0.0, le=2.0)


class JobRequirementCreate(JobRequirementBase):
    pass


class JobRequirementResponse(JobRequirementBase):
    id: str
    job_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    department: str = Field(..., min_length=2, max_length=100)
    raw_description: str = Field(..., min_length=10)
    status: Optional[JobStatus] = "draft"
    requirements: Optional[List[JobRequirementCreate]] = []


class JobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    department: Optional[str] = Field(None, min_length=2, max_length=100)
    raw_description: Optional[str] = Field(None, min_length=10)
    status: Optional[JobStatus] = None
    optimized_description: Optional[str] = None
    requirements: Optional[List[JobRequirementCreate]] = None


class JobStatusUpdate(BaseModel):
    status: JobStatus


class JobResponse(BaseModel):
    id: str
    org_id: str
    created_by_user_id: str
    title: str
    department: str
    status: str
    raw_description: str
    optimized_description: Optional[str] = None
    parsed_criteria: Dict[str, Any] = {}
    bias_risk_score: Optional[float] = None
    bias_findings: Optional[List[Dict[str, Any]]] = None
    requirements: List[JobRequirementResponse] = []
    candidate_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
