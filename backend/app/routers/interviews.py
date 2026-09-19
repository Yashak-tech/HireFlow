"""
Interview Router (Phase 5).

Endpoints:
  POST /api/interviews/prepare       — Generate roadmap & rubric for candidate-job pair
  POST /api/interviews/{id}/turn     — Process candidate turn in the interview
  GET  /api/interviews/{id}/stream   — SSE streaming live transcript (placeholder)
  GET  /api/interviews               — List interviews for the organization
  GET  /api/interviews/{id}          — Get interview details
"""
import logging
import json
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.candidate_match import CandidateMatch
from app.models.candidate_skill import CandidateSkill
from app.models.evidence import Evidence
from app.models.interview import Interview
from app.models.interview_question import InterviewQuestion
from app.models.interview_answer import InterviewAnswer
from app.models.evaluation import Evaluation
from app.models.base import utc_now
from app.schemas.interview import (
    InterviewPrepareRequest,
    InterviewPrepareResponse,
    InterviewTurnRequest,
    InterviewTurnResponse,
    InterviewOut,
    InterviewQuestionOut,
    InterviewAnswerOut,
    InterviewListItem,
    InterviewStreamEvent,
    EvaluationOut,
    HumanDecisionRequest,
)
from app.agents.interview_planner import plan_interview
from app.agents.screening_controller import (
    InterviewState,
    process_interview_turn,
)
from app.agents.interview_evaluator import evaluate_interview
from app.services.audit import log_audit_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/interviews", tags=["Interviews"])


def serialize_interview(interview: Interview) -> InterviewOut:
    """Convert Interview ORM model to Pydantic output schema."""
    return InterviewOut(
        id=interview.id,
        job_id=interview.job_id,
        candidate_id=interview.candidate_id,
        match_id=interview.match_id,
        created_by_user_id=interview.created_by_user_id,
        status=interview.status,
        current_question_index=interview.current_question_index,
        tamper_flag=interview.tamper_flag,
        tamper_details=interview.tamper_details,
        started_at=interview.started_at,
        completed_at=interview.completed_at,
        created_at=interview.created_at,
        updated_at=interview.updated_at,
        questions=[
            InterviewQuestionOut(
                id=q.id,
                order_index=q.order_index,
                category=q.category,
                question_text=q.question_text,
                intent=q.intent,
                targeted_gap=q.targeted_gap,
                rubric_criteria=q.rubric_criteria or {},
                is_customized=q.is_customized,
            )
            for q in sorted(interview.questions, key=lambda x: x.order_index)
        ],
        answers=[
            InterviewAnswerOut(
                id=a.id,
                question_id=a.question_id,
                transcript_text=a.transcript_text,
                attempt_number=a.attempt_number,
                follow_up_prompt=a.follow_up_prompt,
                duration_seconds=a.duration_seconds,
                created_at=a.created_at,
            )
            for a in sorted(interview.answers, key=lambda x: x.created_at)
        ],
        job_title=interview.job.title if interview.job else None,
        candidate_name=interview.candidate.full_name if interview.candidate else None,
    )


# ─── POST /api/interviews/prepare ────────────────────────────────────────

@router.post("/prepare", response_model=InterviewPrepareResponse)
async def prepare_interview(
    request: InterviewPrepareRequest,
    current_user: User = Depends(require_role(["recruiter", "hiring_manager"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a 5-category interview roadmap and rubric for a candidate-job pair.
    Creates an Interview session with pre-generated questions.
    """
    # 1. Validate job belongs to user's org
    job_stmt = (
        select(Job)
        .where(Job.id == request.job_id, Job.org_id == current_user.org_id)
        .options(selectinload(Job.requirements))
    )
    job = (await db.execute(job_stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{request.job_id}' not found in your organization.",
        )

    # 2. Validate candidate belongs to user's org
    cand_stmt = (
        select(Candidate)
        .where(Candidate.id == request.candidate_id, Candidate.org_id == current_user.org_id)
        .options(selectinload(Candidate.skills))
    )
    candidate = (await db.execute(cand_stmt)).scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{request.candidate_id}' not found in your organization.",
        )

    # 3. Find match record for gap data
    match_record = None
    match_id = request.match_id
    if not match_id:
        match_stmt = select(CandidateMatch).where(
            CandidateMatch.job_id == job.id,
            CandidateMatch.candidate_id == candidate.id,
        )
        match_record = (await db.execute(match_stmt)).scalar_one_or_none()
        if match_record:
            match_id = match_record.id
    else:
        m_stmt = select(CandidateMatch).where(CandidateMatch.id == match_id)
        match_record = (await db.execute(m_stmt)).scalar_one_or_none()

    matched_skills = match_record.matched_skills if match_record else []
    missing_skills = match_record.missing_skills if match_record else []
    candidate_skill_names = [s.skill_name for s in (candidate.skills or [])]

    # 4. Generate interview roadmap
    questions_data, roadmap_summary = await plan_interview(
        job_title=job.title,
        job_description=job.raw_description,
        candidate_name=candidate.full_name,
        candidate_skills=candidate_skill_names,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        years_of_experience=float(candidate.years_of_experience) if candidate.years_of_experience else None,
        parsed_criteria=job.parsed_criteria,
    )

    # 5. Create Interview session
    interview = Interview(
        job_id=job.id,
        candidate_id=candidate.id,
        match_id=match_id,
        created_by_user_id=current_user.id,
        status=InterviewState.SCHEDULED,
        current_question_index=0,
        tamper_flag=False,
    )
    db.add(interview)
    await db.flush()

    # 6. Create InterviewQuestion records
    for q_data in questions_data:
        question = InterviewQuestion(
            interview_id=interview.id,
            order_index=q_data["order_index"],
            category=q_data["category"],
            question_text=q_data["question_text"],
            intent=q_data["intent"],
            targeted_gap=q_data.get("targeted_gap"),
            rubric_criteria=q_data.get("rubric_criteria", {}),
            is_customized=False,
        )
        db.add(question)

    # 7. Update match pipeline stage if applicable
    if match_record and match_record.pipeline_stage in ("matched", "evaluated"):
        match_record.pipeline_stage = "screening_prep"

    await db.commit()

    # Reload with relationships
    result_stmt = (
        select(Interview)
        .where(Interview.id == interview.id)
        .options(
            selectinload(Interview.questions),
            selectinload(Interview.answers),
            selectinload(Interview.job),
            selectinload(Interview.candidate),
        )
    )
    interview = (await db.execute(result_stmt)).scalar_one()

    return InterviewPrepareResponse(
        interview=serialize_interview(interview),
        roadmap_summary=roadmap_summary,
        message=f"Interview prepared with {len(questions_data)} questions for {candidate.full_name}.",
    )


# ─── POST /api/interviews/{id}/turn ──────────────────────────────────────

@router.post("/{interview_id}/turn", response_model=InterviewTurnResponse)
async def process_turn(
    interview_id: str,
    request: InterviewTurnRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Process a candidate's answer turn.
    Runs anti-tamper check, evaluates answer quality, advances state machine.
    """
    # 1. Load interview with questions
    int_stmt = (
        select(Interview)
        .where(Interview.id == interview_id)
        .options(
            selectinload(Interview.questions),
            selectinload(Interview.answers),
            selectinload(Interview.job),
            selectinload(Interview.candidate),
        )
    )
    interview = (await db.execute(int_stmt)).scalar_one_or_none()
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview '{interview_id}' not found.",
        )

    # Verify organization isolation through the job
    job_check = await db.execute(
        select(Job).where(Job.id == interview.job_id, Job.org_id == current_user.org_id)
    )
    if not job_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this interview.",
        )

    # 2. Validate interview is in a processable state
    if interview.status in (InterviewState.COMPLETED, InterviewState.ABORTED, InterviewState.CANCELLED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Interview is already '{interview.status}'. Cannot process more turns.",
        )

    # Start the interview if it's in scheduled state
    if interview.status == InterviewState.SCHEDULED:
        interview.status = InterviewState.IN_PROGRESS
        interview.started_at = utc_now()

    # 3. Get current and next questions
    sorted_questions = sorted(interview.questions, key=lambda q: q.order_index)
    total_questions = len(sorted_questions)
    current_idx = interview.current_question_index

    if current_idx >= total_questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All questions have been answered. Interview should be finalized.",
        )

    current_question = sorted_questions[current_idx]
    next_question = sorted_questions[current_idx + 1] if current_idx + 1 < total_questions else None

    # Count existing attempts for this question
    existing_attempts = [
        a for a in interview.answers
        if a.question_id == current_question.id
    ]
    attempt_number = len(existing_attempts) + 1

    # 4. Process through screening controller state machine
    turn_result = process_interview_turn(
        candidate_input=request.candidate_input,
        current_status=interview.status,
        current_question_index=current_idx,
        total_questions=total_questions,
        candidate_name=interview.candidate.full_name if interview.candidate else "Candidate",
        current_question_text=current_question.question_text,
        next_question_text=next_question.question_text if next_question else None,
        attempt_number=attempt_number,
    )

    # 5. Save the answer
    if turn_result["should_save_answer"]:
        answer = InterviewAnswer(
            question_id=current_question.id,
            interview_id=interview.id,
            transcript_text=request.candidate_input,
            attempt_number=attempt_number,
            follow_up_prompt=turn_result.get("follow_up_prompt"),
        )
        db.add(answer)

    # 6. Update interview state
    interview.status = turn_result["new_status"]
    interview.current_question_index = turn_result["new_question_index"]

    if turn_result["tamper_flag"]:
        interview.tamper_flag = True
        interview.tamper_details = turn_result["tamper_details"]
        interview.completed_at = utc_now()

        # Update match pipeline stage
        if interview.match_id:
            match_stmt = select(CandidateMatch).where(CandidateMatch.id == interview.match_id)
            match_record = (await db.execute(match_stmt)).scalar_one_or_none()
            if match_record:
                match_record.pipeline_stage = "interview_active"

    if turn_result["new_status"] == InterviewState.COMPLETED:
        interview.completed_at = utc_now()
        # Update match pipeline stage
        if interview.match_id:
            match_stmt = select(CandidateMatch).where(CandidateMatch.id == interview.match_id)
            match_record = (await db.execute(match_stmt)).scalar_one_or_none()
            if match_record:
                match_record.pipeline_stage = "evaluated"

    await db.commit()

    # Build response
    answered_q = InterviewQuestionOut(
        id=current_question.id,
        order_index=current_question.order_index,
        category=current_question.category,
        question_text=current_question.question_text,
        intent=current_question.intent,
        targeted_gap=current_question.targeted_gap,
        rubric_criteria=current_question.rubric_criteria or {},
        is_customized=current_question.is_customized,
    )

    next_q = None
    # Determine what the next question should be based on updated index
    updated_idx = turn_result["new_question_index"]
    if updated_idx < total_questions and turn_result["new_status"] == InterviewState.IN_PROGRESS:
        nq = sorted_questions[updated_idx]
        next_q = InterviewQuestionOut(
            id=nq.id,
            order_index=nq.order_index,
            category=nq.category,
            question_text=nq.question_text,
            intent=nq.intent,
            targeted_gap=nq.targeted_gap,
            rubric_criteria=nq.rubric_criteria or {},
            is_customized=nq.is_customized,
        )

    return InterviewTurnResponse(
        interview_id=interview.id,
        status=interview.status,
        current_question_index=interview.current_question_index,
        total_questions=total_questions,
        tamper_flag=interview.tamper_flag,
        tamper_details=interview.tamper_details,
        answered_question=answered_q,
        next_question=next_q,
        follow_up_prompt=turn_result.get("follow_up_prompt"),
        ai_message=turn_result["ai_message"],
    )


# ─── GET /api/interviews/{id}/stream ─────────────────────────────────────

@router.get("/{interview_id}/stream")
async def stream_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    SSE streaming endpoint for live interview transcript updates.
    Returns current interview state as SSE events.
    """
    # Load interview
    int_stmt = (
        select(Interview)
        .where(Interview.id == interview_id)
        .options(
            selectinload(Interview.questions),
            selectinload(Interview.answers),
            selectinload(Interview.job),
            selectinload(Interview.candidate),
        )
    )
    interview = (await db.execute(int_stmt)).scalar_one_or_none()
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview '{interview_id}' not found.",
        )

    # Verify org isolation
    job_check = await db.execute(
        select(Job).where(Job.id == interview.job_id, Job.org_id == current_user.org_id)
    )
    if not job_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    async def event_generator():
        """Generate SSE events with current interview state."""
        sorted_questions = sorted(interview.questions, key=lambda q: q.order_index)

        # Send initial state
        init_event = InterviewStreamEvent(
            event_type="progress",
            interview_id=interview.id,
            data={
                "status": interview.status,
                "current_question_index": interview.current_question_index,
                "total_questions": len(sorted_questions),
                "tamper_flag": interview.tamper_flag,
                "candidate_name": interview.candidate.full_name if interview.candidate else "",
                "job_title": interview.job.title if interview.job else "",
            },
        )
        yield f"data: {init_event.model_dump_json()}\n\n"

        # Send transcript of all answered questions
        for q in sorted_questions:
            q_answers = [a for a in interview.answers if a.question_id == q.id]
            for ans in sorted(q_answers, key=lambda a: a.created_at):
                turn_event = InterviewStreamEvent(
                    event_type="transcript",
                    interview_id=interview.id,
                    data={
                        "question_index": q.order_index,
                        "category": q.category,
                        "question_text": q.question_text,
                        "answer_text": ans.transcript_text,
                        "attempt_number": ans.attempt_number,
                        "follow_up": ans.follow_up_prompt,
                    },
                )
                yield f"data: {turn_event.model_dump_json()}\n\n"

        # Send completion marker
        complete_event = InterviewStreamEvent(
            event_type="complete",
            interview_id=interview.id,
            data={"status": interview.status, "tamper_flag": interview.tamper_flag},
        )
        yield f"data: {complete_event.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ─── GET /api/interviews ─────────────────────────────────────────────────

@router.get("", response_model=List[InterviewListItem])
async def list_interviews(
    job_id: Optional[str] = None,
    candidate_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List interviews with optional filters, scoped to user's organization."""
    # Build query joining through Job for org isolation
    stmt = (
        select(Interview)
        .join(Job, Interview.job_id == Job.id)
        .where(Job.org_id == current_user.org_id)
        .options(
            selectinload(Interview.questions),
            selectinload(Interview.job),
            selectinload(Interview.candidate),
            selectinload(Interview.evaluation),
        )
        .order_by(Interview.created_at.desc())
    )

    if job_id:
        stmt = stmt.where(Interview.job_id == job_id)
    if candidate_id:
        stmt = stmt.where(Interview.candidate_id == candidate_id)
    if status_filter:
        stmt = stmt.where(Interview.status == status_filter)

    result = await db.execute(stmt)
    interviews = result.scalars().all()

    items = []
    for iv in interviews:
        items.append(InterviewListItem(
            id=iv.id,
            job_id=iv.job_id,
            candidate_id=iv.candidate_id,
            status=iv.status,
            tamper_flag=iv.tamper_flag,
            current_question_index=iv.current_question_index,
            total_questions=len(iv.questions),
            job_title=iv.job.title if iv.job else None,
            candidate_name=iv.candidate.full_name if iv.candidate else None,
            created_at=iv.created_at,
            started_at=iv.started_at,
            completed_at=iv.completed_at,
            has_evaluation=iv.evaluation is not None,
        ))

    return items


# ─── GET /api/interviews/{id} ────────────────────────────────────────────

@router.get("/{interview_id}", response_model=InterviewOut)
async def get_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full interview details including questions and answers."""
    int_stmt = (
        select(Interview)
        .where(Interview.id == interview_id)
        .options(
            selectinload(Interview.questions),
            selectinload(Interview.answers),
            selectinload(Interview.job),
            selectinload(Interview.candidate),
        )
    )
    interview = (await db.execute(int_stmt)).scalar_one_or_none()
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview '{interview_id}' not found.",
        )

    # Org isolation
    job_check = await db.execute(
        select(Job).where(Job.id == interview.job_id, Job.org_id == current_user.org_id)
    )
    if not job_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    return serialize_interview(interview)


# ─── Evaluation Helper ──────────────────────────────────────────────────

async def generate_and_save_evaluation(
    db: AsyncSession,
    interview: Interview,
    current_user_id: Optional[str] = None,
) -> Evaluation:
    """Generate and persist post-interview Evaluation and interview Evidence."""
    sorted_q = [
        {
            "id": q.id,
            "category": q.category,
            "question_text": q.question_text,
            "intent": q.intent,
            "rubric_criteria": q.rubric_criteria or {},
        }
        for q in sorted(interview.questions, key=lambda x: x.order_index)
    ]
    sorted_a = [
        {
            "id": a.id,
            "question_id": a.question_id,
            "transcript_text": a.transcript_text,
            "attempt_number": a.attempt_number,
        }
        for a in sorted(interview.answers, key=lambda x: x.created_at)
    ]

    candidate_name = interview.candidate.full_name if interview.candidate else "Candidate"
    job_title = interview.job.title if interview.job else "Target Role"

    eval_data = await evaluate_interview(
        candidate_name=candidate_name,
        job_title=job_title,
        questions=sorted_q,
        answers=sorted_a,
        tamper_flag=interview.tamper_flag,
    )

    eval_stmt = select(Evaluation).where(Evaluation.interview_id == interview.id)
    existing_eval = (await db.execute(eval_stmt)).scalar_one_or_none()

    if existing_eval:
        existing_eval.technical_score = eval_data["technical_score"]
        existing_eval.communication_score = eval_data["communication_score"]
        existing_eval.depth_score = eval_data["depth_score"]
        existing_eval.overall_interview_score = eval_data["overall_interview_score"]
        existing_eval.category_scores = eval_data["category_scores"]
        existing_eval.strengths = eval_data["strengths"]
        existing_eval.weaknesses = eval_data["weaknesses"]
        existing_eval.executive_summary = eval_data["executive_summary"]
        existing_eval.ai_recommendation = eval_data["ai_recommendation"]
        evaluation = existing_eval
    else:
        evaluation = Evaluation(
            interview_id=interview.id,
            match_id=interview.match_id,
            technical_score=eval_data["technical_score"],
            communication_score=eval_data["communication_score"],
            depth_score=eval_data["depth_score"],
            overall_interview_score=eval_data["overall_interview_score"],
            category_scores=eval_data["category_scores"],
            strengths=eval_data["strengths"],
            weaknesses=eval_data["weaknesses"],
            executive_summary=eval_data["executive_summary"],
            ai_recommendation=eval_data["ai_recommendation"],
        )
        db.add(evaluation)

    # Grounded Evidence Generation for Interview Answers
    for ev in eval_data.get("evidence_items", []):
        if interview.candidate_id and ev.get("verbatim_source_text"):
            interview_evidence = Evidence(
                candidate_id=interview.candidate_id,
                answer_id=ev.get("answer_id"),
                claim_type=ev.get("claim_type", "interview_demonstration"),
                claim_text=ev.get("claim_text", "Demonstrated skill during live interview."),
                verbatim_source_text=ev.get("verbatim_source_text", ""),
                source_type="interview",
                confidence_score=ev.get("confidence_score", 0.90),
            )
            db.add(interview_evidence)

    # Sync candidate match pipeline stage
    if interview.match_id:
        match_stmt = select(CandidateMatch).where(CandidateMatch.id == interview.match_id)
        match_record = (await db.execute(match_stmt)).scalar_one_or_none()
        if match_record and match_record.pipeline_stage != "offer_extended":
            match_record.pipeline_stage = "evaluated"

    await db.commit()
    await db.refresh(evaluation)

    # Log audit event
    org_id = interview.job.org_id if interview.job else ""
    if org_id:
        await log_audit_event(
            db=db,
            org_id=org_id,
            action="evaluation_generated",
            entity_type="evaluation",
            entity_id=evaluation.id,
            user_id=current_user_id,
            details={
                "interview_id": interview.id,
                "overall_score": evaluation.overall_interview_score,
                "ai_recommendation": evaluation.ai_recommendation,
            },
        )

    return evaluation


# ─── POST /api/interviews/{id}/finalize ──────────────────────────────────

@router.post("/{interview_id}/finalize", response_model=EvaluationOut)
async def finalize_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Explicitly finalize an interview session and generate/refresh the evaluation report.
    """
    int_stmt = (
        select(Interview)
        .where(Interview.id == interview_id)
        .options(
            selectinload(Interview.questions),
            selectinload(Interview.answers),
            selectinload(Interview.job),
            selectinload(Interview.candidate),
        )
    )
    interview = (await db.execute(int_stmt)).scalar_one_or_none()
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview '{interview_id}' not found.",
        )

    # Verify org isolation
    job_check = await db.execute(
        select(Job).where(Job.id == interview.job_id, Job.org_id == current_user.org_id)
    )
    if not job_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    if interview.status != InterviewState.COMPLETED and interview.status != InterviewState.ABORTED:
        interview.status = InterviewState.COMPLETED
        interview.completed_at = utc_now()
        await db.commit()

    evaluation = await generate_and_save_evaluation(db, interview, current_user.id)

    # Log finalize audit event
    await log_audit_event(
        db=db,
        org_id=current_user.org_id,
        action="interview_finalized",
        entity_type="interview",
        entity_id=interview.id,
        user_id=current_user.id,
        details={"status": interview.status, "evaluation_id": evaluation.id},
    )

    return EvaluationOut.model_validate(evaluation)


# ─── GET /api/interviews/{id}/evaluation ─────────────────────────────────

@router.get("/{interview_id}/evaluation", response_model=EvaluationOut)
async def get_interview_evaluation(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve the evaluation report for an interview session.
    If not yet generated, auto-generates if the interview has recorded answers.
    """
    int_stmt = (
        select(Interview)
        .where(Interview.id == interview_id)
        .options(
            selectinload(Interview.questions),
            selectinload(Interview.answers),
            selectinload(Interview.job),
            selectinload(Interview.candidate),
        )
    )
    interview = (await db.execute(int_stmt)).scalar_one_or_none()
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview '{interview_id}' not found.",
        )

    job_check = await db.execute(
        select(Job).where(Job.id == interview.job_id, Job.org_id == current_user.org_id)
    )
    if not job_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    eval_stmt = select(Evaluation).where(Evaluation.interview_id == interview_id)
    evaluation = (await db.execute(eval_stmt)).scalar_one_or_none()

    if not evaluation:
        if len(interview.answers) > 0:
            evaluation = await generate_and_save_evaluation(db, interview, current_user.id)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation has not been generated for this interview session yet.",
            )

    return EvaluationOut.model_validate(evaluation)


# ─── POST /api/interviews/{id}/evaluation/decision ──────────────────────

@router.post("/{interview_id}/evaluation/decision", response_model=EvaluationOut)
async def submit_human_decision(
    interview_id: str,
    payload: HumanDecisionRequest,
    current_user: User = Depends(require_role(["recruiter", "hiring_manager"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Record human recruiter final decision on candidate evaluation.
    Enforces Human-in-the-Loop governance: AI only provides decision support.
    """
    int_stmt = (
        select(Interview)
        .where(Interview.id == interview_id)
        .options(
            selectinload(Interview.job),
            selectinload(Interview.candidate),
        )
    )
    interview = (await db.execute(int_stmt)).scalar_one_or_none()
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview '{interview_id}' not found.",
        )

    job_check = await db.execute(
        select(Job).where(Job.id == interview.job_id, Job.org_id == current_user.org_id)
    )
    if not job_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    eval_stmt = select(Evaluation).where(Evaluation.interview_id == interview_id)
    evaluation = (await db.execute(eval_stmt)).scalar_one_or_none()
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation record not found for this interview.",
        )

    # Update human decision fields
    evaluation.human_decision = payload.decision
    evaluation.human_decision_notes = payload.notes
    evaluation.human_decision_by_user_id = current_user.id
    evaluation.human_decision_at = utc_now()

    # Update CandidateMatch pipeline stage accordingly
    if interview.match_id:
        match_stmt = select(CandidateMatch).where(CandidateMatch.id == interview.match_id)
        match_record = (await db.execute(match_stmt)).scalar_one_or_none()
        if match_record:
            if payload.decision in ("offer_extended", "offer"):
                match_record.pipeline_stage = "offer_extended"
            elif payload.decision in ("rejected", "reject"):
                match_record.pipeline_stage = "rejected"
            elif payload.decision in ("advanced", "advance"):
                match_record.pipeline_stage = "advanced"
            elif payload.decision in ("on_hold", "hold"):
                match_record.pipeline_stage = "on_hold"

    await db.commit()
    await db.refresh(evaluation)

    # Log recruiter final decision audit event
    await log_audit_event(
        db=db,
        org_id=current_user.org_id,
        action="recruiter_decision",
        entity_type="evaluation",
        entity_id=evaluation.id,
        user_id=current_user.id,
        details={
            "decision": payload.decision,
            "notes": payload.notes,
            "candidate_id": interview.candidate_id,
            "job_id": interview.job_id,
        },
    )

    return EvaluationOut.model_validate(evaluation)

