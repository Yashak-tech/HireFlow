"""
Interview Planner Agent (Phase 5).

Analyzes candidate missing gaps and target role criteria to synthesize a
5-Category Interview Roadmap with explicit hiring intents and a pre-generated
Objective Scoring Rubric per TRD §2.8 step 4 and IMPLEMENTATION_PLAN Phase 5.

Categories: technical_depth, gap_probe, behavioral, culture_fit, situational
"""
import json
import logging
import re
from typing import List, Dict, Any, Optional, Tuple

from app.core.config import settings
from app.schemas.interview import InterviewQuestionOut

logger = logging.getLogger(__name__)

# ─── Category definitions ───────────────────────────────────────────────

QUESTION_CATEGORIES = [
    "technical_depth",
    "gap_probe",
    "behavioral",
    "culture_fit",
    "situational",
]

CATEGORY_DESCRIPTIONS = {
    "technical_depth": "Verify depth of claimed technical expertise with concrete implementation questions.",
    "gap_probe": "Probe specific skill or experience gaps identified in the resume-job matching analysis.",
    "behavioral": "Assess teamwork, conflict resolution, and professional conduct through past scenarios.",
    "culture_fit": "Evaluate alignment with team values, work style, and collaboration approach.",
    "situational": "Present hypothetical job-relevant scenarios to test problem-solving and decision-making.",
}


def generate_interview_roadmap_deterministic(
    job_title: str,
    job_description: str,
    candidate_name: str,
    candidate_skills: List[str],
    matched_skills: List[Dict[str, Any]],
    missing_skills: List[Dict[str, Any]],
    years_of_experience: Optional[float] = None,
    parsed_criteria: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Generate a 5-category interview question roadmap using deterministic logic.
    Each question targets specific gaps or verification needs.

    This is the primary grounded implementation — reliable without LLM dependency.
    """
    questions: List[Dict[str, Any]] = []

    # Extract relevant job context
    required_skills = []
    if parsed_criteria:
        required_skills = parsed_criteria.get("required_skills", [])
        if not required_skills:
            required_skills = parsed_criteria.get("must_have", [])

    missing_skill_names = [m.get("skill", m) if isinstance(m, dict) else str(m) for m in missing_skills]
    matched_skill_names = [m.get("skill", m) if isinstance(m, dict) else str(m) for m in matched_skills]

    # Q1: Technical Depth — verify strongest claimed skill
    strongest_skill = matched_skill_names[0] if matched_skill_names else (candidate_skills[0] if candidate_skills else "your primary technology")
    questions.append({
        "order_index": 0,
        "category": "technical_depth",
        "question_text": (
            f"You listed {strongest_skill} as a key skill. Can you walk me through a complex, "
            f"production-level project where you used {strongest_skill}? Specifically, describe "
            f"the architecture decisions you made, challenges you faced, and how you resolved them."
        ),
        "intent": f"Verify depth and hands-on experience with {strongest_skill} beyond surface-level familiarity.",
        "targeted_gap": None,
        "rubric_criteria": {
            "correctness": f"Provides accurate, specific technical details about {strongest_skill} usage in production.",
            "depth": "Demonstrates understanding of trade-offs, architecture patterns, and debugging strategies.",
            "communication": "Explains complex concepts clearly and structures the response logically.",
        },
    })

    # Q2: Gap Probe — target the most critical missing skill
    if missing_skill_names:
        primary_gap = missing_skill_names[0]
        questions.append({
            "order_index": 1,
            "category": "gap_probe",
            "question_text": (
                f"Our {job_title} role requires experience with {primary_gap}, which we didn't "
                f"find explicitly in your background. Have you worked with {primary_gap} or "
                f"similar technologies? How would you approach ramping up on {primary_gap} "
                f"if you joined this team?"
            ),
            "intent": f"Assess transferable skills and learning capacity for the identified gap: {primary_gap}.",
            "targeted_gap": primary_gap,
            "rubric_criteria": {
                "correctness": f"Demonstrates awareness of {primary_gap} concepts or closely related alternatives.",
                "depth": "Shows concrete learning plan or transferable experience from similar technologies.",
                "communication": "Honestly acknowledges the gap while demonstrating willingness and ability to learn.",
            },
        })
    else:
        # If no gaps, ask about extending skills
        questions.append({
            "order_index": 1,
            "category": "gap_probe",
            "question_text": (
                f"Your skills align well with our {job_title} requirements. "
                f"Tell me about a time you had to learn a completely new technology or framework "
                f"under time pressure. How did you approach it and what was the outcome?"
            ),
            "intent": "Assess learning agility and adaptability even when no specific gap exists.",
            "targeted_gap": "general_learning_capacity",
            "rubric_criteria": {
                "correctness": "Provides a specific, verifiable example of rapid skill acquisition.",
                "depth": "Describes concrete learning strategies and measurable outcomes.",
                "communication": "Clearly structures the narrative with context, action, and result.",
            },
        })

    # Q3: Behavioral — teamwork / conflict
    questions.append({
        "order_index": 2,
        "category": "behavioral",
        "question_text": (
            "Tell me about a time you disagreed with a technical decision made by a senior team member. "
            "How did you handle the situation, and what was the outcome?"
        ),
        "intent": "Evaluate conflict resolution, professional communication, and ability to influence without authority.",
        "targeted_gap": None,
        "rubric_criteria": {
            "correctness": "Describes a real, specific situation with identifiable stakeholders and context.",
            "depth": "Shows thoughtful approach to disagreement — data-driven advocacy, not confrontation.",
            "communication": "Demonstrates emotional intelligence and professional maturity.",
        },
    })

    # Q4: Culture Fit
    questions.append({
        "order_index": 3,
        "category": "culture_fit",
        "question_text": (
            f"What does your ideal engineering team culture look like? "
            f"How do you prefer to receive and give feedback? "
            f"What work environment brings out your best performance?"
        ),
        "intent": "Assess cultural alignment with team values, collaboration style, and growth mindset.",
        "targeted_gap": None,
        "rubric_criteria": {
            "correctness": "Provides specific, genuine preferences rather than generic answers.",
            "depth": "Shows self-awareness about personal work style and how it impacts team dynamics.",
            "communication": "Expresses values and preferences clearly and authentically.",
        },
    })

    # Q5: Situational — job-relevant scenario
    second_gap = missing_skill_names[1] if len(missing_skill_names) > 1 else None
    scenario_context = second_gap or (required_skills[0] if required_skills else job_title)
    questions.append({
        "order_index": 4,
        "category": "situational",
        "question_text": (
            f"Imagine you join our team and on your first week, a critical production issue arises "
            f"related to {scenario_context}. The senior engineer who built the system is unavailable. "
            f"Walk me through your approach to diagnosing and resolving this issue."
        ),
        "intent": f"Test problem-solving under pressure and ability to navigate unfamiliar systems related to {scenario_context}.",
        "targeted_gap": second_gap,
        "rubric_criteria": {
            "correctness": "Proposes a systematic, logical debugging approach (logs, monitoring, rollback).",
            "depth": "Considers escalation paths, communication with stakeholders, and documentation.",
            "communication": "Structures the response as a clear action plan with priorities.",
        },
    })

    return questions


async def generate_interview_roadmap_llm(
    job_title: str,
    job_description: str,
    candidate_name: str,
    candidate_skills: List[str],
    matched_skills: List[Dict[str, Any]],
    missing_skills: List[Dict[str, Any]],
    years_of_experience: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Generate a 5-category interview roadmap using LLM.
    Falls back to deterministic if LLM fails.
    """
    from app.services.intelligence_extractor import call_openai_chat_completion

    matched_names = [m.get("skill", m) if isinstance(m, dict) else str(m) for m in matched_skills]
    missing_names = [m.get("skill", m) if isinstance(m, dict) else str(m) for m in missing_skills]

    system_prompt = (
        "You are an expert technical interview planner for recruitment. "
        "Generate exactly 5 interview questions for a candidate, one per category:\n"
        "1. technical_depth — verify claimed skill depth\n"
        "2. gap_probe — probe missing skills identified in matching\n"
        "3. behavioral — past scenario evaluating teamwork/conflict\n"
        "4. culture_fit — alignment with team values and work style\n"
        "5. situational — hypothetical job-relevant problem solving\n\n"
        "Each question must include: question_text, intent, targeted_gap (if applicable), "
        "and rubric_criteria (with correctness, depth, communication fields).\n"
        "Return ONLY valid JSON: {\"questions\": [...]}"
    )

    user_prompt = (
        f"Job Title: {job_title}\n"
        f"Job Description: {job_description[:3000]}\n\n"
        f"Candidate: {candidate_name}\n"
        f"Years of Experience: {years_of_experience or 'Unknown'}\n"
        f"Verified Skills: {', '.join(matched_names[:10])}\n"
        f"Missing Gaps: {', '.join(missing_names[:10])}\n\n"
        "Generate 5 targeted questions."
    )

    try:
        raw_response = await call_openai_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        parsed = json.loads(raw_response)
        raw_questions = parsed.get("questions", [])

        questions = []
        for i, q in enumerate(raw_questions[:5]):
            questions.append({
                "order_index": i,
                "category": QUESTION_CATEGORIES[i] if i < len(QUESTION_CATEGORIES) else "technical_depth",
                "question_text": q.get("question_text", ""),
                "intent": q.get("intent", ""),
                "targeted_gap": q.get("targeted_gap"),
                "rubric_criteria": q.get("rubric_criteria", {}),
            })

        if len(questions) == 5:
            return questions

    except Exception as e:
        logger.warning("LLM interview planning failed, using deterministic: %s", e)

    return generate_interview_roadmap_deterministic(
        job_title=job_title,
        job_description=job_description,
        candidate_name=candidate_name,
        candidate_skills=candidate_skills,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        years_of_experience=years_of_experience,
    )


async def plan_interview(
    job_title: str,
    job_description: str,
    candidate_name: str,
    candidate_skills: List[str],
    matched_skills: List[Dict[str, Any]],
    missing_skills: List[Dict[str, Any]],
    years_of_experience: Optional[float] = None,
    parsed_criteria: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Main entry point for interview planning.
    Returns (questions, roadmap_summary).
    """
    api_key = settings.OPENAI_API_KEY or ""
    use_llm = api_key and not api_key.startswith("sk-mock") and "development" not in api_key.lower()

    if use_llm:
        questions = await generate_interview_roadmap_llm(
            job_title=job_title,
            job_description=job_description,
            candidate_name=candidate_name,
            candidate_skills=candidate_skills,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            years_of_experience=years_of_experience,
        )
    else:
        questions = generate_interview_roadmap_deterministic(
            job_title=job_title,
            job_description=job_description,
            candidate_name=candidate_name,
            candidate_skills=candidate_skills,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            years_of_experience=years_of_experience,
            parsed_criteria=parsed_criteria,
        )

    missing_names = [m.get("skill", m) if isinstance(m, dict) else str(m) for m in missing_skills[:3]]
    matched_names = [m.get("skill", m) if isinstance(m, dict) else str(m) for m in matched_skills[:3]]

    summary_parts = [
        f"Interview roadmap for {candidate_name} — {job_title}.",
        f"5 questions across categories: {', '.join(QUESTION_CATEGORIES)}.",
    ]
    if matched_names:
        summary_parts.append(f"Verifying: {', '.join(matched_names)}.")
    if missing_names:
        summary_parts.append(f"Probing gaps: {', '.join(missing_names)}.")

    return questions, " ".join(summary_parts)
