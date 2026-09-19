from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.db import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.models.candidate_match import CandidateMatch
from app.schemas.job import (
    JobCreate,
    JobUpdate,
    JobStatusUpdate,
    JobResponse,
    JobRequirementResponse,
)
from app.schemas.intelligence import ParseJobResponse
from app.services.intelligence_extractor import extract_job_criteria
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


async def build_job_response(job: Job, db: AsyncSession) -> JobResponse:
    """Helper to assemble JobResponse with candidate counts and requirements."""
    # Count associated candidates via candidate_matches
    count_stmt = select(func.count(CandidateMatch.id)).where(CandidateMatch.job_id == job.id)
    count_res = await db.execute(count_stmt)
    candidate_count = count_res.scalar() or 0

    return JobResponse(
        id=job.id,
        org_id=job.org_id,
        created_by_user_id=job.created_by_user_id,
        title=job.title,
        department=job.department,
        status=job.status,
        raw_description=job.raw_description,
        optimized_description=job.optimized_description,
        parsed_criteria=job.parsed_criteria or {},
        bias_risk_score=job.bias_risk_score,
        bias_findings=job.bias_findings or [],
        requirements=[
            JobRequirementResponse.model_validate(req) for req in (job.requirements or [])
        ],
        candidate_count=candidate_count,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobCreate,
    current_user: User = Depends(require_role(["recruiter", "hiring_manager"])),
    db: AsyncSession = Depends(get_db),
):
    """Create a new job requisition scoped to the authenticated user's organization."""
    new_job = Job(
        org_id=current_user.org_id,
        created_by_user_id=current_user.id,
        title=payload.title,
        department=payload.department,
        raw_description=payload.raw_description,
        status=payload.status or "draft",
        parsed_criteria={
            "title": payload.title,
            "department": payload.department,
            "auto_extracted": False,
        },
    )
    db.add(new_job)
    await db.flush()

    if payload.requirements:
        for req in payload.requirements:
            new_req = JobRequirement(
                job_id=new_job.id,
                requirement_text=req.requirement_text,
                requirement_type=req.requirement_type,
                category=req.category,
                weight=req.weight,
            )
            db.add(new_req)
        await db.flush()

    await db.commit()
    await db.refresh(new_job)

    await log_audit_event(
        db=db,
        org_id=current_user.org_id,
        action="job_created",
        entity_type="job",
        entity_id=new_job.id,
        user_id=current_user.id,
        details={"title": new_job.title, "department": new_job.department},
    )

    return await build_job_response(new_job, db)


@router.get("", response_model=List[JobResponse])
async def list_jobs(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all jobs for the current organization with optional status filtering."""
    query = (
        select(Job)
        .where(Job.org_id == current_user.org_id)
        .order_by(Job.created_at.desc())
    )
    if status_filter:
        query = query.where(Job.status == status_filter)

    result = await db.execute(query)
    jobs = result.scalars().all()

    return [await build_job_response(j, db) for j in jobs]


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single job by ID. Strictly scoped to the authenticated organization."""
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.org_id == current_user.org_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found or does not belong to your organization.",
        )

    return await build_job_response(job, db)


@router.put("/{job_id}", response_model=JobResponse)
@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    payload: JobUpdate,
    current_user: User = Depends(require_role(["recruiter", "hiring_manager"])),
    db: AsyncSession = Depends(get_db),
):
    """Update job details, criteria, or requirements."""
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.org_id == current_user.org_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found or does not belong to your organization.",
        )

    if payload.title is not None:
        job.title = payload.title
    if payload.department is not None:
        job.department = payload.department
    if payload.raw_description is not None:
        job.raw_description = payload.raw_description
    if payload.status is not None:
        job.status = payload.status
    if payload.optimized_description is not None:
        job.optimized_description = payload.optimized_description

    # If requirements were explicitly provided, replace them
    if payload.requirements is not None:
        # Delete existing
        for old_req in job.requirements:
            await db.delete(old_req)
        await db.flush()

        for req in payload.requirements:
            new_req = JobRequirement(
                job_id=job.id,
                requirement_text=req.requirement_text,
                requirement_type=req.requirement_type,
                category=req.category,
                weight=req.weight,
            )
            db.add(new_req)

    await db.commit()
    await db.refresh(job)

    return await build_job_response(job, db)


@router.patch("/{job_id}/status", response_model=JobResponse)
async def update_job_status(
    job_id: str,
    payload: JobStatusUpdate,
    current_user: User = Depends(require_role(["recruiter", "hiring_manager"])),
    db: AsyncSession = Depends(get_db),
):
    """Update only the status of a job (e.g. draft -> active -> paused -> closed)."""
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.org_id == current_user.org_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found or does not belong to your organization.",
        )

    job.status = payload.status
    await db.commit()
    await db.refresh(job)

    return await build_job_response(job, db)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    current_user: User = Depends(require_role(["recruiter", "hiring_manager"])),
    db: AsyncSession = Depends(get_db),
):
    """Delete a job requisition. Cascades cleanly to requirements and matches."""
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.org_id == current_user.org_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found or does not belong to your organization.",
        )

    await db.delete(job)
    await db.commit()
    return None


@router.post("/{job_id}/parse-jd", response_model=ParseJobResponse)
async def parse_job_description(
    job_id: str,
    current_user: User = Depends(require_role(["recruiter", "hiring_manager"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Phase 3: Trigger document intelligence extraction on a job description.
    Extracts structured must_have, nice_to_have, and responsibilities,
    and synchronizes job_requirements.
    """
    stmt = select(Job).where(Job.id == job_id, Job.org_id == current_user.org_id)
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found or does not belong to your organization.",
        )

    # Extract structured criteria
    criteria = await extract_job_criteria(job.raw_description)
    job.parsed_criteria = criteria.model_dump()

    # Clear previous requirements on re-extraction to avoid stale duplicates
    req_stmt = select(JobRequirement).where(JobRequirement.job_id == job.id)
    existing_reqs = (await db.execute(req_stmt)).scalars().all()
    for r in existing_reqs:
        await db.delete(r)
    await db.flush()

    must_have_count = 0
    nice_to_have_count = 0
    resp_count = 0
    seen_texts = set()

    # 1. Add Must Have requirements with smart categorization
    for item in criteria.must_have:
        item_clean = item.strip()
        if not item_clean or item_clean.lower() in seen_texts:
            continue

        lower = item_clean.lower()
        if any(w in lower for w in ["bachelor", "master", "phd", "degree", "computer science", "engineering"]):
            cat = "education"
            weight = 0.9
        elif any(w in lower for w in ["year", "years", "yrs", "experience", "seniority"]):
            cat = "experience"
            weight = 1.3
        else:
            cat = "skill"
            weight = 1.2

        req = JobRequirement(
            job_id=job.id,
            requirement_text=item_clean,
            requirement_type="must_have",
            category=cat,
            weight=weight,
        )
        db.add(req)
        seen_texts.add(item_clean.lower())
        must_have_count += 1

    # 2. Add Nice to Have / Preferred
    for item in criteria.nice_to_have:
        item_clean = item.strip()
        if not item_clean or item_clean.lower() in seen_texts:
            continue

        req = JobRequirement(
            job_id=job.id,
            requirement_text=item_clean,
            requirement_type="nice_to_have",
            category="skill",
            weight=0.8,
        )
        db.add(req)
        seen_texts.add(item_clean.lower())
        nice_to_have_count += 1

    # 3. Add Core Responsibilities
    for item in criteria.responsibilities:
        item_clean = item.strip()
        if not item_clean or item_clean.lower() in seen_texts:
            continue

        req = JobRequirement(
            job_id=job.id,
            requirement_text=item_clean,
            requirement_type="must_have",
            category="domain",
            weight=1.0,
        )
        db.add(req)
        seen_texts.add(item_clean.lower())
        resp_count += 1

    await db.commit()
    await db.refresh(job)

    await log_audit_event(
        db=db,
        org_id=current_user.org_id,
        action="jd_parsed",
        entity_type="job",
        entity_id=job.id,
        user_id=current_user.id,
        details={
            "must_have_count": len(criteria.must_have),
            "nice_to_have_count": len(criteria.nice_to_have),
        },
    )

    return ParseJobResponse(
        job_id=job.id,
        parsed_criteria=job.parsed_criteria,
        must_have_count=len(criteria.must_have),
        nice_to_have_count=len(criteria.nice_to_have),
        responsibilities_count=len(criteria.responsibilities),
    )

