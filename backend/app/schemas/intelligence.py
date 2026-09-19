from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ClaimEvidence(BaseModel):
    source_type: str = Field(default="resume", description="Document source: resume, jd, portfolio")
    verbatim_source_text: str = Field(..., description="Exact textual excerpt from the source document")
    confidence: float = Field(default=0.95, ge=0.0, le=1.0, description="Extraction confidence score (0.0 - 1.0)")


class ExtractedSkill(BaseModel):
    name: str = Field(..., min_length=1, description="Canonical name of the skill")
    category: str = Field(default="technical", description="technical, soft, framework, tool, domain")
    proficiency_level: Optional[str] = Field(None, description="e.g. Expert, Proficient, Familiar")
    years_experience: Optional[float] = Field(None, ge=0.0, le=50.0)
    evidence: Optional[ClaimEvidence] = None


class ExtractedExperience(BaseModel):
    company: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    description: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)
    evidence: Optional[ClaimEvidence] = None


class ExtractedProject(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    link: Optional[str] = None
    evidence: Optional[ClaimEvidence] = None


class ExtractedEducation(BaseModel):
    institution: str = Field(..., min_length=1)
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    grade_or_gpa: Optional[str] = None
    evidence: Optional[ClaimEvidence] = None


class ExtractedCertification(BaseModel):
    name: str = Field(..., min_length=1)
    issuer: Optional[str] = None
    issue_year: Optional[int] = None
    evidence: Optional[ClaimEvidence] = None


class ExtractedLink(BaseModel):
    platform: str = Field(..., description="linkedin, github, portfolio, website, other")
    url: str


class CandidateStructuredProfile(BaseModel):
    """
    Authoritative Pydantic schema for structured candidate profile intelligence.
    Every claim retains provenance/source evidence.
    """
    candidate_summary: Optional[str] = None
    skills: List[ExtractedSkill] = Field(default_factory=list)
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    years_of_experience: Optional[float] = Field(None, ge=0.0, le=50.0)
    work_experience: List[ExtractedExperience] = Field(default_factory=list)
    projects: List[ExtractedProject] = Field(default_factory=list)
    education: List[ExtractedEducation] = Field(default_factory=list)
    certifications: List[ExtractedCertification] = Field(default_factory=list)
    links: List[ExtractedLink] = Field(default_factory=list)
    notable_achievements: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class JobStructuredCriteria(BaseModel):
    """
    Authoritative Pydantic schema for structured job description intelligence.
    Distinguishes MUST HAVE, NICE TO HAVE, RESPONSIBILITIES, and REQUIREMENTS.
    """
    role: Optional[str] = None
    domain: Optional[str] = None
    seniority: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list, description="Must-have technical and domain skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Nice-to-have / preferred skills")
    must_have: List[str] = Field(default_factory=list, description="Core mandatory qualifications or criteria")
    nice_to_have: List[str] = Field(default_factory=list, description="Desirable or secondary qualifications")
    experience_requirements: List[str] = Field(default_factory=list)
    education_requirements: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class ParseResumeResponse(BaseModel):
    resume_id: str
    candidate_id: str
    parsing_status: str
    char_count: int
    word_count: int
    parsed_profile: Dict[str, Any]
    skills_extracted_count: int
    evidence_items_count: int


class ParseJobResponse(BaseModel):
    job_id: str
    parsed_criteria: Dict[str, Any]
    must_have_count: int
    nice_to_have_count: int
    responsibilities_count: int
