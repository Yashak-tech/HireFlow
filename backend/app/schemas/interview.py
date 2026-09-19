"""
Pydantic schemas for Interview Intelligence Agent (Phase 5).
Covers interview preparation, turn-taking, and evaluation responses.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ─── Request Schemas ────────────────────────────────────────────────────

class InterviewPrepareRequest(BaseModel):
    """Request to prepare an interview session for a candidate-job pair."""
    job_id: str
    candidate_id: str
    match_id: Optional[str] = None


class InterviewTurnRequest(BaseModel):
    """Candidate's response to a question during the interview."""
    candidate_input: str = Field(..., min_length=1, max_length=10000)


class InterviewFinalizeRequest(BaseModel):
    """Request to finalize and grade an interview."""
    session_id: Optional[str] = None


class HumanDecisionRequest(BaseModel):
    """Recruiter's human hiring decision on an evaluated candidate."""
    decision: str = Field(..., description="advanced, offer_extended, rejected, on_hold")
    notes: Optional[str] = Field(None, max_length=5000, description="Recruiter rationale & hiring notes")



# ─── Question & Answer Schemas ──────────────────────────────────────────

class RubricCriteria(BaseModel):
    """Pre-generated scoring rubric for a single question."""
    correctness: str = ""
    depth: str = ""
    communication: str = ""


class InterviewQuestionOut(BaseModel):
    """Question output in the interview roadmap."""
    id: str
    order_index: int
    category: str  # technical_depth, gap_probe, behavioral, culture_fit, situational
    question_text: str
    intent: str
    targeted_gap: Optional[str] = None
    rubric_criteria: Dict[str, Any] = {}
    is_customized: bool = False

    model_config = ConfigDict(from_attributes=True)


class InterviewAnswerOut(BaseModel):
    """Answer output from a candidate's response."""
    id: str
    question_id: str
    transcript_text: str
    attempt_number: int = 1
    follow_up_prompt: Optional[str] = None
    duration_seconds: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Interview Session Schemas ──────────────────────────────────────────

class InterviewOut(BaseModel):
    """Full interview session output."""
    id: str
    job_id: str
    candidate_id: str
    match_id: Optional[str] = None
    created_by_user_id: str
    status: str
    current_question_index: int
    tamper_flag: bool
    tamper_details: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    questions: List[InterviewQuestionOut] = []
    answers: List[InterviewAnswerOut] = []

    # Enriched fields (populated when returned)
    job_title: Optional[str] = None
    candidate_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InterviewPrepareResponse(BaseModel):
    """Response after preparing an interview — includes roadmap and rubric."""
    interview: InterviewOut
    roadmap_summary: str
    message: str


class InterviewTurnResponse(BaseModel):
    """Response from processing a candidate's turn in the interview."""
    interview_id: str
    status: str  # in_progress, completed, aborted
    current_question_index: int
    total_questions: int
    tamper_flag: bool
    tamper_details: Optional[Dict[str, Any]] = None

    # The question the candidate just answered
    answered_question: Optional[InterviewQuestionOut] = None
    # The next question (if interview not complete)
    next_question: Optional[InterviewQuestionOut] = None
    # Follow-up prompt if answer was vague
    follow_up_prompt: Optional[str] = None
    # AI feedback message
    ai_message: str = ""


class InterviewStreamEvent(BaseModel):
    """SSE event format for live interview streaming."""
    event_type: str  # transcript, progress, turn_update, tamper_alert, complete
    interview_id: str
    data: Dict[str, Any] = {}


# ─── Evaluation Schemas ─────────────────────────────────────────────────

class EvaluationOut(BaseModel):
    """Post-interview evaluation output."""
    id: str
    interview_id: str
    match_id: Optional[str] = None
    technical_score: float
    communication_score: float
    depth_score: float
    overall_interview_score: float
    category_scores: Dict[str, Any] = {}
    strengths: List[str] = []
    weaknesses: List[str] = []
    executive_summary: str
    ai_recommendation: str  # advance, review_needed, reject
    human_decision: Optional[str] = None
    human_decision_notes: Optional[str] = None
    human_decision_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewListItem(BaseModel):
    """Compact interview item for list views."""
    id: str
    job_id: str
    candidate_id: str
    status: str
    tamper_flag: bool
    current_question_index: int
    total_questions: int = 0
    job_title: Optional[str] = None
    candidate_name: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    has_evaluation: bool = False

    model_config = ConfigDict(from_attributes=True)
