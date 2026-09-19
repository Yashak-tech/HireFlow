import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
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
from app.models.resume import Resume
from app.models.job_requirement import JobRequirement
from app.schemas.matching import CandidateMatchCard, MatchRunResponse, RequirementMatchItem
from app.services.matching_engine import evaluate_candidate_match, find_skill_evidence
from app.services.audit import log_audit_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/matching", tags=["Matching"])


async def build_candidate_match_card(
    match: CandidateMatch,
    candidate: Candidate,
    job: Job,
    db: AsyncSession,
) -> CandidateMatchCard:
    """Helper to assemble a rich CandidateMatchCard with requirement-level breakdown."""
    # Load candidate skills and evidence if not eagerly loaded
    skill_stmt = select(CandidateSkill).where(CandidateSkill.candidate_id == candidate.id)
    skills = (await db.execute(skill_stmt)).scalars().all()

    ev_stmt = select(Evidence).where(Evidence.candidate_id == candidate.id)
    evidence_items = (await db.execute(ev_stmt)).scalars().all()

    resume_stmt = select(Resume).where(Resume.candidate_id == candidate.id).order_by(Resume.created_at.desc())
    resumes = (await db.execute(resume_stmt)).scalars().all()
    raw_text = resumes[0].raw_text if resumes else ""

    # Reconstruct requirements breakdown against current job requirements
    req_stmt = select(JobRequirement).where(JobRequirement.job_id == job.id)
    reqs = (await db.execute(req_stmt)).scalars().all()

    requirements_breakdown: List[RequirementMatchItem] = []
    for req in reqs:
        status_val, quote, conf = find_skill_evidence(
            req.requirement_text,
            candidate,
            skills,
            evidence_items,
            raw_text,
        )
        requirements_breakdown.append(
            RequirementMatchItem(
                requirement_id=req.id,
                requirement_text=req.requirement_text,
                requirement_type=req.requirement_type,
                category=req.category,
                weight=req.weight,
                status=status_val,
                evidence_quote=quote,
                confidence=conf,
            )
        )

    return CandidateMatchCard(
        match_id=match.id,
        job_id=match.job_id,
        candidate_id=candidate.id,
        candidate_name=candidate.full_name,
        candidate_email=candidate.email,
        current_title=candidate.current_title,
        current_company=candidate.current_company,
        years_of_experience=candidate.years_of_experience,
        overall_match_score=round(float(match.overall_match_score or 0.0), 1),
        vector_similarity=round(float(match.vector_similarity or 0.0), 4),
        skill_overlap_score=round(float(match.skill_overlap_score or 0.0), 1),
        experience_fit_score=round(float(match.experience_fit_score or 0.0), 1),
        pipeline_stage=match.pipeline_stage,
        reasoning=match.reasoning,
        matched_skills=match.matched_skills or [],
        missing_skills=match.missing_skills or [],
        requirements_breakdown=requirements_breakdown,
        created_at=match.created_at,
        updated_at=match.updated_at,
    )


@router.post("/{job_id}/run", response_model=MatchRunResponse)
@router.post("/{job_id}", response_model=MatchRunResponse)
async def run_candidate_matching(
    job_id: str,
    current_user: User = Depends(require_role(["recruiter", "hiring_manager"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute the Two-Stage Candidate Matching Engine for a job requisition.
    Evaluates all associated candidates (or all candidates in the organization).
    Updates CandidateMatch records with scores, vector similarity, grounded reasoning,
    and advances pipeline_stage to 'evaluated'.
    """
    # 1. Fetch Job and ensure organization isolation
    job_stmt = (
        select(Job)
        .where(Job.id == job_id, Job.org_id == current_user.org_id)
        .options(selectinload(Job.requirements))
    )
    job = (await db.execute(job_stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found or does not belong to your organization.",
        )

    # 2. Find Candidates to evaluate
    # Check candidates currently linked via candidate_matches
    match_stmt = (
        select(CandidateMatch)
        .where(CandidateMatch.job_id == job.id)
    )
    existing_matches = (await db.execute(match_stmt)).scalars().all()
    matched_candidate_ids = {m.candidate_id: m for m in existing_matches}

    if matched_candidate_ids:
        cand_stmt = (
            select(Candidate)
            .where(Candidate.id.in_(list(matched_candidate_ids.keys())), Candidate.org_id == current_user.org_id)
            .options(
                selectinload(Candidate.skills),
                selectinload(Candidate.evidence_items),
                selectinload(Candidate.resumes),
            )
        )
        candidates = (await db.execute(cand_stmt)).scalars().all()
    else:
        # Evaluate all candidates in organization
        cand_stmt = (
            select(Candidate)
            .where(Candidate.org_id == current_user.org_id)
            .options(
                selectinload(Candidate.skills),
                selectinload(Candidate.evidence_items),
                selectinload(Candidate.resumes),
            )
        )
        candidates = (await db.execute(cand_stmt)).scalars().all()

    evaluated_cards: List[CandidateMatchCard] = []

    for cand in candidates:
        # Run two-stage matching engine
        eval_result = await evaluate_candidate_match(
            job=job,
            candidate=cand,
            requirements=job.requirements or [],
            skills=cand.skills or [],
            evidence_items=cand.evidence_items or [],
            resumes=cand.resumes or [],
        )

        match_record = matched_candidate_ids.get(cand.id)
        if not match_record:
            match_record = CandidateMatch(
                job_id=job.id,
                candidate_id=cand.id,
                pipeline_stage="evaluated",
            )
            db.add(match_record)

        match_record.overall_match_score = eval_result["overall_match_score"]
        match_record.vector_similarity = eval_result["vector_similarity"]
        match_record.skill_overlap_score = eval_result["skill_overlap_score"]
        match_record.experience_fit_score = eval_result["experience_fit_score"]
        match_record.reasoning = eval_result["reasoning"]
        match_record.matched_skills = eval_result["matched_skills"]
        match_record.missing_skills = eval_result["missing_skills"]
        # Advance stage from 'matched' to 'evaluated'
        if match_record.pipeline_stage == "matched":
            match_record.pipeline_stage = "evaluated"

        await db.flush()

        card = CandidateMatchCard(
            match_id=match_record.id,
            job_id=job.id,
            candidate_id=cand.id,
            candidate_name=cand.full_name,
            candidate_email=cand.email,
            current_title=cand.current_title,
            current_company=cand.current_company,
            years_of_experience=cand.years_of_experience,
            overall_match_score=eval_result["overall_match_score"],
            vector_similarity=eval_result["vector_similarity"],
            skill_overlap_score=eval_result["skill_overlap_score"],
            experience_fit_score=eval_result["experience_fit_score"],
            pipeline_stage=match_record.pipeline_stage,
            reasoning=eval_result["reasoning"],
            matched_skills=eval_result["matched_skills"],
            missing_skills=eval_result["missing_skills"],
            requirements_breakdown=eval_result["requirements_breakdown"],
            created_at=match_record.created_at,
            updated_at=match_record.updated_at,
        )
        evaluated_cards.append(card)

    await db.commit()

    await log_audit_event(
        db=db,
        org_id=current_user.org_id,
        action="match_analysis_executed",
        entity_type="job",
        entity_id=job.id,
        user_id=current_user.id,
        details={"candidates_evaluated_count": len(evaluated_cards)},
    )

    # Sort descending by overall_match_score
    evaluated_cards.sort(key=lambda c: c.overall_match_score, reverse=True)

    from app.models.base import utc_now

    return MatchRunResponse(
        job_id=job.id,
        job_title=job.title,
        total_candidates_evaluated=len(evaluated_cards),
        matches=evaluated_cards,
        run_at=utc_now(),
    )


@router.get("/{job_id}/results", response_model=List[CandidateMatchCard])
async def get_job_match_results(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve ranked candidate match scorecards for a job requisition."""
    # Ensure job belongs to user's organization
    job_stmt = select(Job).where(Job.id == job_id, Job.org_id == current_user.org_id)
    job = (await db.execute(job_stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found or does not belong to your organization.",
        )

    # Fetch matches joined with candidates
    match_stmt = (
        select(CandidateMatch)
        .where(CandidateMatch.job_id == job.id)
        .order_by(CandidateMatch.overall_match_score.desc())
    )
    matches = (await db.execute(match_stmt)).scalars().all()

    cards: List[CandidateMatchCard] = []
    for match in matches:
        cand_stmt = select(Candidate).where(Candidate.id == match.candidate_id, Candidate.org_id == current_user.org_id)
        cand = (await db.execute(cand_stmt)).scalar_one_or_none()
        if cand:
            card = await build_candidate_match_card(match, cand, job, db)
            cards.append(card)

    return cards


@router.get("/{job_id}/candidate/{candidate_id}", response_model=CandidateMatchCard)
async def get_candidate_job_match(
    job_id: str,
    candidate_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed match scorecard and requirement breakdown for a specific candidate."""
    job_stmt = select(Job).where(Job.id == job_id, Job.org_id == current_user.org_id)
    job = (await db.execute(job_stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found in your organization.",
        )

    cand_stmt = select(Candidate).where(Candidate.id == candidate_id, Candidate.org_id == current_user.org_id)
    cand = (await db.execute(cand_stmt)).scalar_one_or_none()
    if not cand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found in your organization.",
        )

    match_stmt = select(CandidateMatch).where(
        CandidateMatch.job_id == job.id,
        CandidateMatch.candidate_id == cand.id,
    )
    match = (await db.execute(match_stmt)).scalar_one_or_none()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No match record found for candidate '{candidate_id}' on job '{job_id}'.",
        )

    return await build_candidate_match_card(match, cand, job, db)
