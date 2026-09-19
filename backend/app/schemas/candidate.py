from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
import re
from pydantic import BaseModel, Field, ConfigDict, field_validator

SkillCategory = Literal["technical", "framework", "tool", "soft", "domain"]
VerificationStatus = Literal["unverified", "verified_resume", "verified_interview", "challenged"]
ParsingStatus = Literal["pending", "processing", "completed", "failed"]

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class CandidateSkillBase(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=100)
    category: SkillCategory = "technical"
    years_experience: Optional[float] = Field(None, ge=0.0, le=50.0)
    proficiency_level: Optional[str] = Field(None, max_length=50)
    verification_status: VerificationStatus = "unverified"


class CandidateSkillCreate(CandidateSkillBase):
    pass


class CandidateSkillResponse(CandidateSkillBase):
    id: str
    candidate_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeResponse(BaseModel):
    id: str
    candidate_id: str
    file_name: str
    file_path: str
    file_type: str
    file_size_bytes: int
    parsing_status: str
    parsing_error: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssociatedJobSummary(BaseModel):
    job_id: str
    job_title: str
    pipeline_stage: str
    overall_match_score: float
    created_at: datetime


class CandidateCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: str = Field(..., min_length=5, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=150)
    current_title: Optional[str] = Field(None, max_length=150)
    current_company: Optional[str] = Field(None, max_length=150)
    years_of_experience: Optional[float] = Field(None, ge=0.0, le=50.0)
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    job_id: Optional[str] = None  # Optional job to link upon creation
    skills: Optional[List[CandidateSkillCreate]] = []

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        if not EMAIL_REGEX.match(v):
            raise ValueError("Invalid email address format")
        return v.lower().strip()


class CandidateUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[str] = Field(None, min_length=5, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=150)
    current_title: Optional[str] = Field(None, max_length=150)
    current_company: Optional[str] = Field(None, max_length=150)
    years_of_experience: Optional[float] = Field(None, ge=0.0, le=50.0)
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not EMAIL_REGEX.match(v):
                raise ValueError("Invalid email address format")
            return v.lower().strip()
        return v


class CandidateResponse(BaseModel):
    id: str
    org_id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    years_of_experience: Optional[float] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    parsed_profile: Dict[str, Any] = {}
    skills: List[CandidateSkillResponse] = []
    resumes: List[ResumeResponse] = []
    associated_jobs: List[AssociatedJobSummary] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000, description="Natural language search query")


class CandidateQueryMatch(BaseModel):
    candidate: CandidateResponse
    match_score: float
    matched_skills: List[str] = []
    reasoning: str


class CandidateQueryResponse(BaseModel):
    query: str
    parsed_skills: List[str] = []
    parsed_min_experience: Optional[float] = None
    results: List[CandidateQueryMatch] = []

