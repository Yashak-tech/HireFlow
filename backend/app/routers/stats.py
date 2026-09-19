"""
Dashboard Stats Router (Phase 7).
Provides aggregated KPI metrics for the recruiter dashboard.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.job import Job
from app.models.candidate_match import CandidateMatch
from app.models.interview import Interview

router = APIRouter(prefix="/api/stats", tags=["Stats"])


@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Aggregated KPI stats for the recruiter dashboard.
    Returns active requisitions, top matches, average fidelity, and estimated hours saved.
    """
    org_id = current_user.org_id

    # Active job count
    active_jobs_stmt = select(func.count(Job.id)).where(
        Job.org_id == org_id, Job.status == "active"
    )
    active_jobs = (await db.execute(active_jobs_stmt)).scalar() or 0

    # Total matches
    all_matches_stmt = (
        select(CandidateMatch.overall_match_score)
        .join(Job, CandidateMatch.job_id == Job.id)
        .where(Job.org_id == org_id)
    )
    result = await db.execute(all_matches_stmt)
    all_scores = [row[0] for row in result.all() if row[0] is not None]

    top_matches = sum(1 for s in all_scores if s >= 80)
    avg_fidelity = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0

    # Completed interviews count (used for hours-saved estimate)
    completed_interviews_stmt = (
        select(func.count(Interview.id))
        .join(Job, Interview.job_id == Job.id)
        .where(Job.org_id == org_id, Interview.status == "completed")
    )
    completed_interviews = (await db.execute(completed_interviews_stmt)).scalar() or 0

    # Each automated screening saves ~45 min of manual phone screen, each match saves ~15 min
    hours_saved = round(completed_interviews * 0.75 + len(all_scores) * 0.25, 1)

    return {
        "active_requisitions": active_jobs,
        "top_match_candidates": top_matches,
        "avg_match_fidelity": avg_fidelity,
        "hours_saved": hours_saved,
        "total_matches": len(all_scores),
        "completed_interviews": completed_interviews,
    }
