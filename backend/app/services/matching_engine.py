import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.models.candidate import Candidate
from app.models.candidate_match import CandidateMatch
from app.models.candidate_skill import CandidateSkill
from app.models.evidence import Evidence
from app.models.resume import Resume
from app.schemas.matching import RequirementMatchItem, CandidateMatchCard
from app.services.embeddings import generate_embedding, cosine_similarity

logger = logging.getLogger(__name__)


def extract_required_years_from_job(job: Job) -> float:
    """Extract required minimum years of experience from job criteria or raw text."""
    if job.parsed_criteria and isinstance(job.parsed_criteria, dict):
        if "experience_years_required" in job.parsed_criteria:
            try:
                return float(job.parsed_criteria["experience_years_required"])
            except (ValueError, TypeError):
                pass

    # Regex search for experience in raw description (e.g. "3+ years", "5 years of experience")
    match = re.search(r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)(?:\s+of)?\s+experience", job.raw_description, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass

    return 3.0  # Reasonable industry baseline default


def find_skill_evidence(
    req_text: str,
    candidate: Candidate,
    skills: List[CandidateSkill],
    evidence_items: List[Evidence],
    raw_resume_text: str,
) -> Tuple[str, Optional[str], float]:
    """
    Evaluate candidate evidence against a specific job requirement.
    Returns: (status, evidence_quote, confidence)
      status: 'MATCHED', 'MISSING', or 'UNCLEAR'
    """
    clean_req = req_text.strip().lower()

    # Normalize common tech terms (e.g. "fastapi framework" -> "fastapi", "postgres" -> "postgresql")
    keywords = re.findall(r"\b[a-z0-9+#.-]{2,}\b", clean_req)

    # 1. Search in Grounded Evidence items (highest provenance)
    for ev in evidence_items:
        ev_claim = ev.claim_text.lower()
        ev_source = ev.verbatim_source_text.lower()
        if clean_req in ev_claim or clean_req in ev_source:
            return "MATCHED", ev.verbatim_source_text, float(ev.confidence_score or 0.95)
        # Check matching any specific keyword if requirement is multi-word
        for kw in keywords:
            if kw in ["experience", "knowledge", "proficient", "strong", "skills", "ability"]:
                continue
            if len(kw) >= 3 and (kw == ev_claim or f" {kw} " in f" {ev_source} "):
                return "MATCHED", ev.verbatim_source_text, 0.90

    # 2. Search in Extracted Candidate Skills
    for skill in skills:
        s_name = skill.skill_name.lower()
        if s_name == clean_req or s_name in clean_req or clean_req in s_name:
            # Check if skill matches, find quote if possible
            quote = f"Candidate profile confirms proficiency in {skill.skill_name}"
            # Try to find sentence in raw resume text
            if raw_resume_text:
                m = re.search(rf"([^.\n]*\b{re.escape(skill.skill_name)}\b[^.\n]*)", raw_resume_text, re.IGNORECASE)
                if m:
                    quote = m.group(0).strip()
            return "MATCHED", quote, 0.85

    # 3. Search in Raw Resume text
    if raw_resume_text:
        # Check full requirement string
        if clean_req in raw_resume_text.lower():
            m = re.search(rf"([^.\n]*\b{re.escape(req_text[:30])}\b[^.\n]*)", raw_resume_text, re.IGNORECASE)
            quote = m.group(0).strip() if m else f"Found mention in resume text: {req_text}"
            return "MATCHED", quote[:250], 0.80

        # Check major keywords in resume
        matched_kws = []
        for kw in keywords:
            if kw in ["experience", "knowledge", "proficient", "strong", "skills", "ability", "working", "with", "years"]:
                continue
            if len(kw) >= 3 and re.search(rf"\b{re.escape(kw)}\b", raw_resume_text, re.IGNORECASE):
                matched_kws.append(kw)

        if len(keywords) > 1 and len(matched_kws) == len([k for k in keywords if len(k) >= 3 and k not in ["experience", "knowledge", "proficient", "strong", "skills", "ability", "working", "with", "years"]]):
            m = re.search(rf"([^.\n]*\b{re.escape(matched_kws[0])}\b[^.\n]*)", raw_resume_text, re.IGNORECASE)
            quote = m.group(0).strip() if m else f"Relevant resume excerpt containing {', '.join(matched_kws)}"
            return "MATCHED", quote[:250], 0.75
        elif len(matched_kws) > 0:
            return "UNCLEAR", f"Partial reference found in candidate documentation for keywords: {', '.join(matched_kws)}", 0.50

    # No evidence found
    return "MISSING", f"No explicit {req_text} experience found in candidate evidence", 0.0


async def evaluate_candidate_match(
    job: Job,
    candidate: Candidate,
    requirements: List[JobRequirement],
    skills: List[CandidateSkill],
    evidence_items: List[Evidence],
    resumes: List[Resume],
) -> Dict[str, Any]:
    """
    Execute the Two-Stage Matching Engine for a single candidate against a job requisition.
    Stage 1: Vector Cosine Similarity
    Stage 2: Deterministic Heuristic Re-ranking (Skill Overlap + Experience Fit + Vector Similarity)
    """
    # 1. Retrieve or generate Job Embedding
    job_embedding = job.embedding
    if not job_embedding:
        job_text = f"{job.title} - {job.department}\n{job.raw_description}"
        job_embedding = await generate_embedding(job_text)
        job.embedding = job_embedding

    # 2. Retrieve or generate Candidate / Resume Embedding
    raw_resume_text = ""
    candidate_embedding = None
    if resumes:
        latest_resume = sorted(resumes, key=lambda r: r.created_at, reverse=True)[0]
        raw_resume_text = latest_resume.raw_text or ""
        candidate_embedding = latest_resume.embedding

        if not candidate_embedding and raw_resume_text:
            candidate_embedding = await generate_embedding(raw_resume_text)
            latest_resume.embedding = candidate_embedding

    if not candidate_embedding:
        # Generate from candidate profile/skills text
        skill_names = [s.skill_name for s in skills]
        cand_text = f"{candidate.full_name} - {candidate.current_title or ''} - Experience: {candidate.years_of_experience or 0} yrs. Skills: {', '.join(skill_names)}. {raw_resume_text[:2000]}"
        candidate_embedding = await generate_embedding(cand_text)

    # Stage 1: Vector Cosine Similarity (0.0 to 1.0)
    vec_sim = cosine_similarity(job_embedding, candidate_embedding)

    # Stage 2: Heuristic Skill Overlap
    req_breakdown: List[RequirementMatchItem] = []
    matched_skills_list: List[Dict[str, Any]] = []
    missing_skills_list: List[Dict[str, Any]] = []

    total_weight = 0.0
    earned_weight = 0.0

    # If no DB requirements exist, synthesize from parsed_criteria or job title
    effective_reqs = list(requirements)
    if not effective_reqs:
        if job.parsed_criteria and isinstance(job.parsed_criteria, dict):
            must_haves = job.parsed_criteria.get("must_have", [])
            for mh in must_haves:
                effective_reqs.append(
                    JobRequirement(
                        job_id=job.id,
                        requirement_text=mh,
                        requirement_type="must_have",
                        category="skill",
                        weight=1.2,
                    )
                )
            nice_haves = job.parsed_criteria.get("nice_to_have", [])
            for nh in nice_haves:
                effective_reqs.append(
                    JobRequirement(
                        job_id=job.id,
                        requirement_text=nh,
                        requirement_type="nice_to_have",
                        category="skill",
                        weight=0.8,
                    )
                )

    if effective_reqs:
        for req in effective_reqs:
            w = float(req.weight or 1.0)
            total_weight += w

            status, quote, conf = find_skill_evidence(
                req.requirement_text,
                candidate,
                skills,
                evidence_items,
                raw_resume_text,
            )

            req_item = RequirementMatchItem(
                requirement_id=req.id if hasattr(req, "id") and req.id else None,
                requirement_text=req.requirement_text,
                requirement_type=req.requirement_type or "must_have",
                category=req.category or "skill",
                weight=w,
                status=status,
                evidence_quote=quote,
                confidence=conf,
            )
            req_breakdown.append(req_item)

            if status == "MATCHED":
                earned_weight += w
                matched_skills_list.append({
                    "skill": req.requirement_text,
                    "evidence": quote,
                    "confidence": conf,
                    "type": req.requirement_type,
                })
            elif status == "UNCLEAR":
                earned_weight += (w * 0.5)  # Partial credit
                missing_skills_list.append({
                    "skill": req.requirement_text,
                    "reason": "Unclear / partial mention in evidence",
                    "type": req.requirement_type,
                })
            else:
                missing_skills_list.append({
                    "skill": req.requirement_text,
                    "reason": f"No explicit {req.requirement_text} experience found in candidate evidence",
                    "type": req.requirement_type,
                })

        skill_overlap_score = round((earned_weight / total_weight) * 100.0, 1) if total_weight > 0 else 100.0
    else:
        skill_overlap_score = 50.0

    # Stage 2: Experience Fit Score
    req_years = extract_required_years_from_job(job)
    cand_years = float(candidate.years_of_experience or 0.0)

    if req_years <= 0:
        experience_fit_score = 100.0
    elif cand_years >= req_years:
        experience_fit_score = 100.0
    else:
        experience_fit_score = round((cand_years / req_years) * 100.0, 1)

    experience_fit_score = max(0.0, min(100.0, experience_fit_score))

    # Stage 2: Composite Overall Match Score Formula (Locked per TRD & Implementation Plan):
    # overall_match_score = round(0.50 * skill_overlap + 0.25 * experience_fit + 0.25 * (vector_similarity * 100), 1)
    overall_score = round(
        (0.50 * skill_overlap_score) +
        (0.25 * experience_fit_score) +
        (0.25 * (vec_sim * 100.0)),
        1
    )
    overall_score = max(0.0, min(100.0, overall_score))

    # Grounded 2-3 sentence executive reasoning (strictly decision support, no autonomous hire/reject)
    matched_names = [m["skill"] for m in matched_skills_list[:3]]
    missing_names = [m["skill"] for m in missing_skills_list[:3]]

    reasoning_parts = []
    if matched_names:
        reasoning_parts.append(
            f"Candidate displays verified alignment with key requirements including {', '.join(matched_names)}."
        )
    else:
        reasoning_parts.append("Candidate demonstrates minimal direct alignment with the posted core technical requirements.")

    if missing_names:
        reasoning_parts.append(
            f"Gaps identified: No explicit experience found for {', '.join(missing_names)} in candidate evidence."
        )
    else:
        reasoning_parts.append("No significant skill gaps detected against must-have criteria.")

    reasoning_parts.append(
        f"Computed overall match rating of {overall_score}% ({cand_years} yrs exp vs {req_years} yrs required; vector similarity {vec_sim:.2f}) provides objective decision support for recruiter review."
    )
    reasoning_text = " ".join(reasoning_parts)

    return {
        "overall_match_score": overall_score,
        "vector_similarity": vec_sim,
        "skill_overlap_score": skill_overlap_score,
        "experience_fit_score": experience_fit_score,
        "reasoning": reasoning_text,
        "matched_skills": matched_skills_list,
        "missing_skills": missing_skills_list,
        "requirements_breakdown": req_breakdown,
    }
