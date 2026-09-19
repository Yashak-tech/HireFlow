import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.candidate import Candidate
from app.models.candidate_skill import CandidateSkill
from app.models.resume import Resume
from app.models.candidate_match import CandidateMatch
from app.models.job import Job
from app.models.evidence import Evidence
from app.schemas.candidate import (
    CandidateCreate,
    CandidateUpdate,
    CandidateResponse,
    CandidateSkillResponse,
    ResumeResponse,
    AssociatedJobSummary,
    CandidateQueryRequest,
    CandidateQueryResponse,
    CandidateQueryMatch,
)
from app.schemas.evidence import EvidenceResponse, EvidenceOverride
from app.schemas.intelligence import ParseResumeResponse
from app.services.file_storage import validate_and_save_resume_file
from app.services.document_parser import parse_document_file
from app.services.intelligence_extractor import (
    extract_candidate_profile,
    mask_demographics_for_evaluation,
)
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/candidates", tags=["Candidates"])


async def build_candidate_response(candidate: Candidate, db: AsyncSession) -> CandidateResponse:
    """Helper to assemble full CandidateResponse with skills, resumes, and associated jobs."""
    # Fetch associated jobs through candidate_matches
    matches_stmt = (
        select(CandidateMatch, Job.title)
        .join(Job, CandidateMatch.job_id == Job.id)
        .where(CandidateMatch.candidate_id == candidate.id)
    )
    matches_res = await db.execute(matches_stmt)
    associated_jobs = [
        AssociatedJobSummary(
            job_id=m.CandidateMatch.job_id,
            job_title=m.title,
            pipeline_stage=m.CandidateMatch.pipeline_stage,
            overall_match_score=m.CandidateMatch.overall_match_score,
            created_at=m.CandidateMatch.created_at,
        )
        for m in matches_res.all()
    ]

    return CandidateResponse(
        id=candidate.id,
        org_id=candidate.org_id,
        full_name=candidate.full_name,
        email=candidate.email,
        phone=candidate.phone,
        location=candidate.location,
        current_title=candidate.current_title,
        current_company=candidate.current_company,
        years_of_experience=candidate.years_of_experience,
        linkedin_url=candidate.linkedin_url,
        github_url=candidate.github_url,
        portfolio_url=candidate.portfolio_url,
        parsed_profile=candidate.parsed_profile or {},
        skills=[CandidateSkillResponse.model_validate(s) for s in (candidate.skills or [])],
        resumes=[ResumeResponse.model_validate(r) for r in (candidate.resumes or [])],
        associated_jobs=associated_jobs,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at,
    )


@router.post("", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def create_candidate(
    payload: CandidateCreate,
    current_user: User = Depends(require_role(["recruiter", "hiring_manager"])),
    db: AsyncSession = Depends(get_db),
):
    """Create a new candidate profile in the recruiter's organization."""
    # Check if candidate email already exists in this org
    existing_stmt = select(Candidate).where(
        Candidate.org_id == current_user.org_id,
        Candidate.email == payload.email,
    )
    existing_res = await db.execute(existing_stmt)
    if existing_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Candidate with email '{payload.email}' already exists in your organization.",
        )

    candidate = Candidate(
        org_id=current_user.org_id,
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        location=payload.location,
        current_title=payload.current_title,
        current_company=payload.current_company,
        years_of_experience=payload.years_of_experience,
        linkedin_url=payload.linkedin_url,
        github_url=payload.github_url,
        portfolio_url=payload.portfolio_url,
        parsed_profile={
            "source": "manual_entry",
            "full_name": payload.full_name,
        },
    )
    db.add(candidate)
    await db.flush()

    # Add skills if provided
    if payload.skills:
        for sk in payload.skills:
            skill = CandidateSkill(
                candidate_id=candidate.id,
                skill_name=sk.skill_name,
                category=sk.category,
                years_experience=sk.years_experience,
                proficiency_level=sk.proficiency_level,
                verification_status=sk.verification_status,
            )
            db.add(skill)
        await db.flush()

    # Associate with job if job_id was specified
    if payload.job_id:
        # Verify job belongs to this org
        job_stmt = select(Job).where(Job.id == payload.job_id, Job.org_id == current_user.org_id)
        job_res = await db.execute(job_stmt)
        job = job_res.scalar_one_or_none()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job '{payload.job_id}' not found in your organization.",
            )

        match = CandidateMatch(
            job_id=job.id,
            candidate_id=candidate.id,
            overall_match_score=0.0,
            pipeline_stage="matched",
            reasoning="Candidate added to job requisition.",
        )
        db.add(match)
        await db.flush()

    await db.commit()
    await db.refresh(candidate)

    return await build_candidate_response(candidate, db)


@router.get("", response_model=List[CandidateResponse])
async def list_candidates(
    job_id: Optional[str] = Query(None, description="Filter candidates associated with a specific job"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List candidates belonging to the user's organization, optionally filtered by job association."""
    if job_id:
        query = (
            select(Candidate)
            .join(CandidateMatch, Candidate.id == CandidateMatch.candidate_id)
            .where(
                Candidate.org_id == current_user.org_id,
                CandidateMatch.job_id == job_id,
            )
            .order_by(Candidate.created_at.desc())
        )
    else:
        query = (
            select(Candidate)
            .where(Candidate.org_id == current_user.org_id)
            .order_by(Candidate.created_at.desc())
        )

    result = await db.execute(query)
    candidates = result.scalars().all()

    return [await build_candidate_response(c, db) for c in candidates]


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed candidate profile by ID. Strictly scoped to current organization."""
    result = await db.execute(
        select(Candidate).where(
            Candidate.id == candidate_id,
            Candidate.org_id == current_user.org_id,
        )
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found or does not belong to your organization.",
        )

    return await build_candidate_response(candidate, db)


@router.put("/{candidate_id}", response_model=CandidateResponse)
@router.patch("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    candidate_id: str,
    payload: CandidateUpdate,
    current_user: User = Depends(require_role(["recruiter", "hiring_manager"])),
    db: AsyncSession = Depends(get_db),
):
    """Update candidate basic information."""
    result = await db.execute(
        select(Candidate).where(
            Candidate.id == candidate_id,
            Candidate.org_id == current_user.org_id,
        )
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found or does not belong to your organization.",
        )

    if payload.full_name is not None:
        candidate.full_name = payload.full_name
    if payload.email is not None:
        # Check uniqueness in org if changed
        if payload.email != candidate.email:
            dup_stmt = select(Candidate).where(
                Candidate.org_id == current_user.org_id,
                Candidate.email == payload.email,
                Candidate.id != candidate.id,
            )
            dup = (await db.execute(dup_stmt)).scalar_one_or_none()
            if dup:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Another candidate with email '{payload.email}' already exists.",
                )
        candidate.email = payload.email
    if payload.phone is not None:
        candidate.phone = payload.phone
    if payload.location is not None:
        candidate.location = payload.location
    if payload.current_title is not None:
        candidate.current_title = payload.current_title
    if payload.current_company is not None:
        candidate.current_company = payload.current_company
    if payload.years_of_experience is not None:
        candidate.years_of_experience = payload.years_of_experience
    if payload.linkedin_url is not None:
        candidate.linkedin_url = payload.linkedin_url
    if payload.github_url is not None:
        candidate.github_url = payload.github_url
    if payload.portfolio_url is not None:
        candidate.portfolio_url = payload.portfolio_url

    await db.commit()
    await db.refresh(candidate)

    return await build_candidate_response(candidate, db)


@router.post("/upload", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def upload_candidate_resume(
    file: UploadFile = File(...),
    job_id: Optional[str] = Form(None),
    full_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    current_user: User = Depends(require_role(["recruiter", "hiring_manager"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload and store a candidate resume document (.pdf, .docx, .txt).
    Enforces file type restrictions and 10MB limit.
    Stores using UUID-based safe filename.
    Creates Candidate and Resume record with parsing_status='pending' (Phase 2 boundary).
    """
    # 1. Validate and save file to disk
    original_name, file_path, file_type, file_size = await validate_and_save_resume_file(file)

    # 2. Derive candidate names/email if not provided
    if not full_name:
        # Generate friendly name from filename (e.g. Elena_Rostova_CV.pdf -> Elena Rostova)
        base = os.path.splitext(original_name)[0]
        clean = base.replace("_", " ").replace("-", " ").replace("resume", "").replace("cv", "").strip()
        full_name = clean.title() if clean else "Candidate Profile"

    if not email:
        clean_slug = full_name.lower().replace(" ", ".")
        email = f"{clean_slug}@applicant.hireflow.internal"

    # 3. Check if candidate already exists by email in this org
    candidate_stmt = select(Candidate).where(
        Candidate.org_id == current_user.org_id,
        Candidate.email == email,
    )
    candidate_res = await db.execute(candidate_stmt)
    candidate = candidate_res.scalar_one_or_none()

    if not candidate:
        candidate = Candidate(
            org_id=current_user.org_id,
            full_name=full_name,
            email=email,
            parsed_profile={"source": "resume_upload", "original_filename": original_name},
        )
        db.add(candidate)
        await db.flush()

    # 4. Create Resume record
    resume = Resume(
        candidate_id=candidate.id,
        file_name=original_name,
        file_path=file_path,
        file_type=file_type,
        file_size_bytes=file_size,
        raw_text="",
        parsing_status="pending",
    )
    db.add(resume)
    await db.flush()

    # 5. Associate with job if specified
    if job_id:
        job_stmt = select(Job).where(Job.id == job_id, Job.org_id == current_user.org_id)
        job = (await db.execute(job_stmt)).scalar_one_or_none()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job '{job_id}' not found in your organization.",
            )

        # Check existing match
        match_stmt = select(CandidateMatch).where(
            CandidateMatch.job_id == job.id,
            CandidateMatch.candidate_id == candidate.id,
        )
        match = (await db.execute(match_stmt)).scalar_one_or_none()
        if not match:
            match = CandidateMatch(
                job_id=job.id,
                candidate_id=candidate.id,
                overall_match_score=0.0,
                pipeline_stage="matched",
                reasoning=f"Resume '{original_name}' uploaded for job.",
            )
            db.add(match)
            await db.flush()

    await db.commit()
    await db.refresh(candidate)

    return await build_candidate_response(candidate, db)


@router.post("/{candidate_id}/resume", response_model=CandidateResponse)
async def attach_resume_to_candidate(
    candidate_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(["recruiter", "hiring_manager"])),
    db: AsyncSession = Depends(get_db),
):
    """Attach an additional resume file to an existing candidate profile."""
    result = await db.execute(
        select(Candidate).where(
            Candidate.id == candidate_id,
            Candidate.org_id == current_user.org_id,
        )
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found or does not belong to your organization.",
        )

    original_name, file_path, file_type, file_size = await validate_and_save_resume_file(file)

    resume = Resume(
        candidate_id=candidate.id,
        file_name=original_name,
        file_path=file_path,
        file_type=file_type,
        file_size_bytes=file_size,
        raw_text="",
        parsing_status="pending",
    )
    db.add(resume)
    await db.commit()
    await db.refresh(candidate)

    return await build_candidate_response(candidate, db)


@router.post("/{candidate_id}/associate-job/{job_id}", response_model=CandidateResponse)
async def associate_candidate_with_job(
    candidate_id: str,
    job_id: str,
    current_user: User = Depends(require_role(["recruiter", "hiring_manager"])),
    db: AsyncSession = Depends(get_db),
):
    """Associate a candidate with a specific job requisition."""
    candidate_stmt = select(Candidate).where(
        Candidate.id == candidate_id,
        Candidate.org_id == current_user.org_id,
    )
    candidate = (await db.execute(candidate_stmt)).scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found in your organization.",
        )

    job_stmt = select(Job).where(Job.id == job_id, Job.org_id == current_user.org_id)
    job = (await db.execute(job_stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found in your organization.",
        )

    match_stmt = select(CandidateMatch).where(
        CandidateMatch.job_id == job.id,
        CandidateMatch.candidate_id == candidate.id,
    )
    match = (await db.execute(match_stmt)).scalar_one_or_none()
    if not match:
        match = CandidateMatch(
            job_id=job.id,
            candidate_id=candidate.id,
            overall_match_score=0.0,
            pipeline_stage="matched",
            reasoning="Manually associated with job requisition.",
        )
        db.add(match)
        await db.commit()

    await db.refresh(candidate)
    return await build_candidate_response(candidate, db)


@router.post("/{candidate_id}/parse-resume", response_model=ParseResumeResponse)
async def parse_candidate_resume(
    candidate_id: str,
    resume_id: Optional[str] = Query(None, description="Optional specific resume ID to parse"),
    current_user: User = Depends(require_role(["recruiter", "hiring_manager"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Phase 3: Trigger document intelligence extraction on candidate's uploaded resume.
    Lifecycle: pending -> processing -> completed / failed.
    Extracts structured profile, synchronizes candidate skills, and grounds evidence provenance.
    """
    # Verify candidate exists in user's organization
    candidate_stmt = select(Candidate).where(
        Candidate.id == candidate_id,
        Candidate.org_id == current_user.org_id,
    )
    candidate = (await db.execute(candidate_stmt)).scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found in your organization.",
        )

    # Locate the target resume
    if resume_id:
        resume_stmt = select(Resume).where(
            Resume.id == resume_id,
            Resume.candidate_id == candidate.id,
        )
    else:
        # Latest resume
        resume_stmt = (
            select(Resume)
            .where(Resume.candidate_id == candidate.id)
            .order_by(Resume.created_at.desc())
        )
    resume = (await db.execute(resume_stmt)).scalars().first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No resume document found for candidate '{candidate_id}'.",
        )

    # Transition status: pending -> processing
    resume.parsing_status = "processing"
    resume.parsing_error = None
    await db.commit()

    try:
        # Step 1: Document text extraction (pypdf, pdfplumber, python-docx, native txt)
        parsed_doc = parse_document_file(resume.file_path, resume.file_type)
        resume.raw_text = parsed_doc.raw_text

        # Step 2: Structured extraction with LLM repair loop
        profile = await extract_candidate_profile(parsed_doc.raw_text)
        candidate.parsed_profile = profile.model_dump()

        if profile.years_of_experience is not None and not candidate.years_of_experience:
            candidate.years_of_experience = profile.years_of_experience

        # Step 3: Synchronize extracted skills
        existing_skills_stmt = select(CandidateSkill).where(CandidateSkill.candidate_id == candidate.id)
        existing_skills = (await db.execute(existing_skills_stmt)).scalars().all()
        existing_skill_names = {s.skill_name.lower() for s in existing_skills}

        for s in profile.skills:
            if s.name.lower() not in existing_skill_names:
                cat = s.category if s.category in ["technical", "framework", "tool", "soft", "domain"] else "technical"
                new_skill = CandidateSkill(
                    candidate_id=candidate.id,
                    skill_name=s.name,
                    category=cat,
                    years_experience=s.years_experience,
                    proficiency_level=s.proficiency_level,
                    verification_status="verified_resume" if s.evidence else "unverified",
                )
                db.add(new_skill)
                existing_skill_names.add(s.name.lower())

        # Step 4: Persist grounded Evidence items for provenance
        evidence_count = 0
        for s in profile.skills:
            if s.evidence and s.evidence.verbatim_source_text:
                ev = Evidence(
                    candidate_id=candidate.id,
                    resume_id=resume.id,
                    claim_type="skill",
                    claim_text=s.name,
                    verbatim_source_text=s.evidence.verbatim_source_text,
                    source_type=s.evidence.source_type or "resume",
                    confidence_score=s.evidence.confidence,
                )
                db.add(ev)
                evidence_count += 1

        for exp in profile.work_experience:
            if exp.evidence and exp.evidence.verbatim_source_text:
                ev = Evidence(
                    candidate_id=candidate.id,
                    resume_id=resume.id,
                    claim_type="experience",
                    claim_text=f"{exp.title} at {exp.company}",
                    verbatim_source_text=exp.evidence.verbatim_source_text,
                    source_type=exp.evidence.source_type or "resume",
                    confidence_score=exp.evidence.confidence,
                )
                db.add(ev)
                evidence_count += 1

        for edu in profile.education:
            if edu.evidence and edu.evidence.verbatim_source_text:
                ev = Evidence(
                    candidate_id=candidate.id,
                    resume_id=resume.id,
                    claim_type="education",
                    claim_text=edu.institution,
                    verbatim_source_text=edu.evidence.verbatim_source_text,
                    source_type=edu.evidence.source_type or "resume",
                    confidence_score=edu.evidence.confidence,
                )
                db.add(ev)
                evidence_count += 1

        for proj in profile.projects:
            if proj.evidence and proj.evidence.verbatim_source_text:
                ev = Evidence(
                    candidate_id=candidate.id,
                    resume_id=resume.id,
                    claim_type="project",
                    claim_text=proj.name,
                    verbatim_source_text=proj.evidence.verbatim_source_text,
                    source_type=proj.evidence.source_type or "resume",
                    confidence_score=proj.evidence.confidence,
                )
                db.add(ev)
                evidence_count += 1

        # Transition status: processing -> completed
        resume.parsing_status = "completed"
        resume.parsing_error = None
        await db.commit()
        await db.refresh(resume)
        await db.refresh(candidate)

        return ParseResumeResponse(
            resume_id=resume.id,
            candidate_id=candidate.id,
            parsing_status="completed",
            char_count=len(resume.raw_text),
            word_count=len(resume.raw_text.split()),
            parsed_profile=candidate.parsed_profile,
            skills_extracted_count=len(profile.skills),
            evidence_items_count=evidence_count,
        )

    except HTTPException as exc:
        # Persist failure status and error safely
        resume.parsing_status = "failed"
        resume.parsing_error = str(exc.detail)
        await db.commit()
        raise exc
    except Exception as exc:
        resume.parsing_status = "failed"
        resume.parsing_error = str(exc)
        await db.commit()
        raise HTTPException(
            status_code=422,
            detail=f"Document parsing failed: {str(exc)}",
        )


@router.get("/{candidate_id}/evidence", response_model=List[EvidenceResponse])
async def list_candidate_evidence(
    candidate_id: str,
    current_user: User = Depends(require_role(["recruiter", "hiring_manager"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Phase 3: Retrieve all grounded evidence items and provenance records for a candidate.
    Enforces tenant isolation.
    """
    candidate_stmt = select(Candidate).where(
        Candidate.id == candidate_id,
        Candidate.org_id == current_user.org_id,
    )
    candidate = (await db.execute(candidate_stmt)).scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found in your organization.",
        )

    evidence_stmt = (
        select(Evidence)
        .where(Evidence.candidate_id == candidate.id)
        .order_by(Evidence.created_at.desc())
    )
    evidence_items = (await db.execute(evidence_stmt)).scalars().all()
    return [EvidenceResponse.model_validate(e) for e in evidence_items]


@router.patch("/{candidate_id}/evidence/{evidence_id}/override", response_model=EvidenceResponse)
async def override_candidate_evidence(
    candidate_id: str,
    evidence_id: str,
    payload: EvidenceOverride,
    current_user: User = Depends(require_role(["recruiter", "hiring_manager"])),
    db: AsyncSession = Depends(get_db),
):
    """Allow recruiter to audit/override an evidence item."""
    candidate_stmt = select(Candidate).where(
        Candidate.id == candidate_id,
        Candidate.org_id == current_user.org_id,
    )
    candidate = (await db.execute(candidate_stmt)).scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found in your organization.",
        )

    evidence_stmt = select(Evidence).where(
        Evidence.id == evidence_id,
        Evidence.candidate_id == candidate.id,
    )
    evidence = (await db.execute(evidence_stmt)).scalar_one_or_none()
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence item '{evidence_id}' not found.",
        )

    evidence.is_overridden_by_human = payload.is_overridden_by_human
    evidence.overridden_by_user_id = current_user.id
    evidence.override_reason = payload.override_reason
    await db.commit()
    await db.refresh(evidence)
    return EvidenceResponse.model_validate(evidence)


@router.get("/{candidate_id}/masked-profile")
async def get_candidate_masked_profile(
    candidate_id: str,
    current_user: User = Depends(require_role(["recruiter", "hiring_manager"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Phase 3: Retrieve sanitized evaluation profile with demographics masked.
    Removes candidate name, gender pronouns, graduation dates, and personal links.
    Original raw resume data remains untouched in the database.
    """
    candidate_stmt = select(Candidate).where(
        Candidate.id == candidate_id,
        Candidate.org_id == current_user.org_id,
    )
    candidate = (await db.execute(candidate_stmt)).scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found in your organization.",
        )

    masked = mask_demographics_for_evaluation(
        candidate.parsed_profile or {},
        candidate_name=candidate.full_name,
    )
    return {
        "candidate_id": candidate.id,
        "anonymized_profile": masked,
    }


# ─── Natural-Language Candidate Query (Phase 6) ─────────────────────────

@router.post("/query", response_model=CandidateQueryResponse)
async def query_candidates(
    payload: CandidateQueryRequest,
    current_user: User = Depends(require_role(["recruiter", "hiring_manager"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Phase 6: Natural-language candidate talent pool query.
    Extracts skill requirements, experience thresholds, and domain criteria
    from unstructured prompts and ranks organization candidates against structured data.
    """
    import re
    raw_query = payload.query.strip()
    query_lower = raw_query.lower()

    # 1. Extract years of experience requirement (e.g., "2 years", "at least 3 years", "5+ yrs")
    min_exp = None
    exp_match = re.search(r"(?:at least|min(?:imum)?|>=|\+)?\s*(\d+(?:\.\d+)?)\s*(?:\+|plus)?\s*(?:years?|yrs?)", query_lower)
    if exp_match:
        try:
            min_exp = float(exp_match.group(1))
        except ValueError:
            min_exp = None

    # 2. Known common skills vocabulary for deterministic recognition
    KNOWN_SKILLS = [
        "python", "fastapi", "django", "flask", "postgresql", "postgres", "sql", "mysql",
        "react", "vue", "angular", "next.js", "nextjs", "javascript", "typescript", "node", "nodejs",
        "docker", "kubernetes", "aws", "gcp", "azure", "graphql", "rest", "redis", "mongodb",
        "machine learning", "ml", "ai", "deep learning", "nlp", "llm", "openai", "pytorch",
        "terraform", "ci/cd", "git", "linux", "golang", "go", "rust", "java", "c++", "c#"
    ]

    detected_skills = []
    for skill in KNOWN_SKILLS:
        # Match as whole word or phrase
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, query_lower):
            detected_skills.append(skill)

    # 3. Load all candidates for the organization with skills
    stmt = (
        select(Candidate)
        .where(Candidate.org_id == current_user.org_id)
        .order_by(Candidate.created_at.desc())
    )
    result = await db.execute(stmt)
    candidates = result.scalars().all()

    query_results: List[CandidateQueryMatch] = []

    for cand in candidates:
        cand_resp = await build_candidate_response(cand, db)
        cand_skill_names = [s.skill_name.lower() for s in cand_resp.skills]
        parsed_skills = [s.lower() for s in (cand.parsed_profile.get("skills") or [])]
        all_cand_skills = set(cand_skill_names + parsed_skills)

        # Match detected skills
        matched_skills = [s for s in detected_skills if any(s in cs for cs in all_cand_skills)]
        
        # Calculate match score
        skill_score = (len(matched_skills) / len(detected_skills) * 100) if detected_skills else 50.0

        # Experience score modifier
        exp_score = 100.0
        exp_reasons = []
        if min_exp is not None:
            cand_exp = cand.years_of_experience or 0.0
            if cand_exp >= min_exp:
                exp_score = 100.0
                exp_reasons.append(f"Experience: {cand_exp} yrs (meets >={min_exp} yrs target)")
            else:
                exp_score = max(20.0, (cand_exp / min_exp) * 80.0)
                exp_reasons.append(f"Experience: {cand_exp} yrs (below {min_exp} yrs target)")
        elif cand.years_of_experience:
            exp_reasons.append(f"Experience: {cand.years_of_experience} yrs")

        # Free-text token overlap
        profile_text = f"{cand.full_name} {cand.current_title or ''} {cand.current_company or ''} {cand.location or ''}".lower()
        free_text_matches = [w for w in query_lower.split() if len(w) > 3 and w in profile_text and w not in detected_skills]

        total_score = round(0.65 * skill_score + 0.35 * exp_score, 1)

        # Build grounded reasoning
        reasoning_parts = []
        if matched_skills:
            reasoning_parts.append(f"Matched Skills: {', '.join(s.title() for s in matched_skills)}.")
        if exp_reasons:
            reasoning_parts.append(" ".join(exp_reasons) + ".")
        if free_text_matches:
            reasoning_parts.append(f"Profile mentions: {', '.join(free_text_matches)}.")
        if not reasoning_parts:
            reasoning_parts.append("Profile indexed in organization talent pool.")

        reasoning = " ".join(reasoning_parts)

        # Include if has any matched skill, meets exp, or free text match (or if query had no specific filter)
        if matched_skills or (min_exp is not None and cand.years_of_experience and cand.years_of_experience >= min_exp) or not detected_skills:
            query_results.append(
                CandidateQueryMatch(
                    candidate=cand_resp,
                    match_score=total_score,
                    matched_skills=matched_skills,
                    reasoning=reasoning,
                )
            )

    # Sort descending by match score
    query_results.sort(key=lambda x: x.match_score, reverse=True)

    return CandidateQueryResponse(
        query=raw_query,
        parsed_skills=detected_skills,
        parsed_min_experience=min_exp,
        results=query_results,
    )


