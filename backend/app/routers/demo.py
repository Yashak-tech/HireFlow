"""
Demo Seed Router (Phase 7).
Seeds demo data for hackathon demonstration. Only available in development/demo environments.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.models.candidate import Candidate
from app.models.candidate_skill import CandidateSkill
from app.models.resume import Resume
from app.models.candidate_match import CandidateMatch
from app.models.interview import Interview
from app.models.interview_question import InterviewQuestion
from app.models.interview_answer import InterviewAnswer
from app.models.evaluation import Evaluation
from app.models.evidence import Evidence
from app.models.audit_log import AuditLog
from app.models.base import utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/demo", tags=["Demo"])


@router.post("/seed")
async def seed_demo_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Seeds realistic demo data for hackathon presentation.
    Only available in development/demo environments.
    Requires authentication to prevent unauthorized data mutations.
    """
    if settings.ENVIRONMENT not in ("development", "demo", "testing", "test"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo seeding is only available in development/demo environments.",
        )

    org_id = current_user.org_id

    try:
        # ── 1. Create Software Engineering Job ────────────────────────
        job = Job(
            org_id=org_id,
            created_by_user_id=current_user.id,
            title="Senior Full-Stack Engineer",
            department="Engineering",
            raw_description=(
                "We are looking for a Senior Full-Stack Engineer to join our platform team. "
                "You will design and build scalable microservices, implement responsive React UIs, "
                "and drive engineering best practices across the organization. "
                "Requirements: 5+ years experience, proficiency in Python, TypeScript, React, "
                "PostgreSQL, Docker, and cloud platforms (AWS/GCP). Experience with CI/CD pipelines, "
                "system design, and mentoring junior engineers is highly valued."
            ),
            status="active",
            parsed_criteria={
                "must_have": ["Python", "TypeScript", "React", "PostgreSQL", "Docker"],
                "nice_to_have": ["AWS", "GCP", "Kubernetes", "CI/CD", "System Design"],
                "experience_range": "5-12 years",
            },
        )
        db.add(job)
        await db.flush()

        # Add requirements
        requirements = [
            ("Python", "skill", True, 1.5),
            ("TypeScript", "skill", True, 1.2),
            ("React", "skill", True, 1.2),
            ("PostgreSQL", "skill", True, 1.2),
            ("Docker", "skill", True, 1.0),
            ("AWS/GCP Cloud", "skill", False, 0.8),
            ("CI/CD Pipelines", "domain", False, 0.8),
            ("System Design", "domain", False, 1.2),
            ("Team Leadership", "domain", False, 0.9),
        ]
        for skill_name, category, is_required, weight in requirements:
            req = JobRequirement(
                job_id=job.id,
                requirement_text=skill_name,
                requirement_type="must_have" if is_required else "nice_to_have",
                category=category,
                weight=weight,
            )
            db.add(req)

        # ── 2. Create Diverse Candidates ──────────────────────────────
        candidates_data = [
            {
                "full_name": "Aisha Patel",
                "email": "aisha.patel@example.com",
                "phone": "+1-555-0101",
                "location": "San Francisco, CA",
                "years_of_experience": 7.0,
                "current_title": "Senior Software Engineer",
                "current_company": "CloudScale Inc.",
                "skills": ["Python", "TypeScript", "React", "PostgreSQL", "Docker", "AWS", "Kubernetes", "CI/CD"],
                "resume_text": (
                    "Aisha Patel — Senior Software Engineer\n"
                    "7 years of experience building high-performance distributed systems.\n\n"
                    "EXPERIENCE:\n"
                    "Senior Software Engineer, CloudScale Inc. (2021–Present)\n"
                    "- Architected microservices platform serving 2M+ daily active users using Python/FastAPI and TypeScript/React\n"
                    "- Designed and optimized PostgreSQL schemas handling 500M+ rows with advanced indexing strategies\n"
                    "- Implemented CI/CD pipelines with GitHub Actions, Docker, and Kubernetes on AWS EKS\n"
                    "- Mentored team of 4 junior engineers on system design and code review practices\n\n"
                    "Software Engineer, TechNova (2018–2021)\n"
                    "- Built real-time analytics dashboard with React, D3.js, and WebSocket streaming\n"
                    "- Developed RESTful APIs in Python/Django processing 10K+ requests/minute\n\n"
                    "EDUCATION: B.S. Computer Science, Stanford University\n"
                    "SKILLS: Python, TypeScript, React, PostgreSQL, Docker, AWS, Kubernetes, CI/CD, System Design, FastAPI"
                ),
            },
            {
                "full_name": "Marcus Chen",
                "email": "marcus.chen@example.com",
                "phone": "+1-555-0102",
                "location": "Seattle, WA",
                "years_of_experience": 4.0,
                "current_title": "Frontend Developer",
                "current_company": "DesignHub",
                "skills": ["TypeScript", "React", "CSS", "Figma", "Node.js", "GraphQL"],
                "resume_text": (
                    "Marcus Chen — Frontend Developer\n"
                    "4 years specializing in modern frontend architectures and design systems.\n\n"
                    "EXPERIENCE:\n"
                    "Frontend Developer, DesignHub (2022–Present)\n"
                    "- Built component library serving 15+ internal products using React and TypeScript\n"
                    "- Implemented responsive layouts and accessibility features (WCAG 2.1 AA)\n"
                    "- Collaborated with UX team on interactive prototypes in Figma\n\n"
                    "Junior Developer, StartupXYZ (2020–2022)\n"
                    "- Developed customer-facing SPA with React and GraphQL\n"
                    "- Built Node.js middleware for API aggregation\n\n"
                    "EDUCATION: B.S. Information Systems, UC Berkeley\n"
                    "SKILLS: TypeScript, React, CSS, Figma, Node.js, GraphQL, HTML, JavaScript"
                ),
            },
            {
                "full_name": "Dr. Elena Rodriguez",
                "email": "elena.rodriguez@example.com",
                "phone": "+1-555-0103",
                "location": "Boston, MA",
                "years_of_experience": 10.0,
                "current_title": "Principal Engineer",
                "current_company": "DataFlow Systems",
                "skills": ["Python", "Java", "PostgreSQL", "System Design", "AWS", "Kafka", "Docker", "Terraform", "Leadership"],
                "resume_text": (
                    "Dr. Elena Rodriguez — Principal Engineer\n"
                    "10 years of experience in large-scale distributed systems and technical leadership.\n\n"
                    "EXPERIENCE:\n"
                    "Principal Engineer, DataFlow Systems (2019–Present)\n"
                    "- Led architecture of event-driven platform processing 1B+ events/day using Kafka and Python\n"
                    "- Designed PostgreSQL sharding strategy reducing query latency by 60%\n"
                    "- Managed team of 12 engineers across 3 product squads\n"
                    "- Drove migration from monolith to microservices on AWS with Docker and Terraform\n\n"
                    "Senior Engineer, MegaCorp (2015–2019)\n"
                    "- Built real-time data pipelines with Java and Apache Spark\n"
                    "- Implemented automated deployment with Jenkins and Docker\n\n"
                    "EDUCATION: Ph.D. Computer Science, MIT\n"
                    "SKILLS: Python, Java, PostgreSQL, System Design, AWS, Kafka, Docker, Terraform, Technical Leadership"
                ),
            },
        ]

        created_candidates = []
        for cand_data in candidates_data:
            candidate = Candidate(
                org_id=org_id,
                full_name=cand_data["full_name"],
                email=cand_data["email"],
                phone=cand_data.get("phone"),
                location=cand_data.get("location"),
                years_of_experience=cand_data["years_of_experience"],
                current_title=cand_data.get("current_title"),
                current_company=cand_data.get("current_company"),
                parsed_profile={
                    "candidate_summary": f"{cand_data['full_name']} has {cand_data['years_of_experience']} years of software engineering experience.",
                    "work_experience": [
                        {
                            "title": cand_data.get("current_title"),
                            "company": cand_data.get("current_company"),
                            "highlights": ["Architected scalable applications", "Collaborated with cross-functional teams"],
                        }
                    ],
                    "skills": cand_data["skills"],
                },
            )
            db.add(candidate)
            await db.flush()

            # Add skills
            for skill_name in cand_data["skills"]:
                skill = CandidateSkill(
                    candidate_id=candidate.id,
                    skill_name=skill_name,
                    category="technical",
                    proficiency_level="advanced",
                    years_experience=cand_data["years_of_experience"] / 2,
                    verification_status="verified_resume",
                )
                db.add(skill)

            # Add resume
            resume = Resume(
                candidate_id=candidate.id,
                file_name=f"{cand_data['full_name'].replace(' ', '_').lower()}_resume.pdf",
                file_path=f"resumes/demo_{candidate.id}.pdf",
                file_type="application/pdf",
                file_size_bytes=len(cand_data["resume_text"].encode()),
                raw_text=cand_data["resume_text"],
                parsing_status="completed",
            )
            db.add(resume)
            created_candidates.append(candidate)

        await db.flush()

        # ── 3. Create Match Records ───────────────────────────────────
        match_data = [
            {
                "candidate_idx": 0,  # Aisha — ideal match
                "overall_score": 92.5,
                "vector_score": 0.94,
                "heuristic_score": 91.0,
                "matched_skills": ["Python", "TypeScript", "React", "PostgreSQL", "Docker", "AWS"],
                "missing_skills": ["GCP"],
                "reasoning": "Exceptional alignment — 6/7 required skills with strong production experience.",
                "pipeline_stage": "evaluated",
            },
            {
                "candidate_idx": 1,  # Marcus — partial match
                "overall_score": 58.3,
                "vector_score": 0.72,
                "heuristic_score": 52.0,
                "matched_skills": ["TypeScript", "React"],
                "missing_skills": ["Python", "PostgreSQL", "Docker"],
                "reasoning": "Strong frontend skills but missing critical backend requirements.",
                "pipeline_stage": "matched",
            },
            {
                "candidate_idx": 2,  # Elena — overqualified
                "overall_score": 87.1,
                "vector_score": 0.89,
                "heuristic_score": 85.0,
                "matched_skills": ["Python", "PostgreSQL", "Docker", "AWS", "System Design"],
                "missing_skills": ["TypeScript", "React"],
                "reasoning": "Excellent backend and leadership experience. Missing frontend framework proficiency.",
                "pipeline_stage": "matched",
            },
        ]

        created_matches = []
        for md in match_data:
            match = CandidateMatch(
                job_id=job.id,
                candidate_id=created_candidates[md["candidate_idx"]].id,
                overall_match_score=md["overall_score"],
                vector_similarity=md["vector_score"],
                skill_overlap_score=md["heuristic_score"],
                experience_fit_score=md["heuristic_score"],
                matched_skills=[{"skill": s, "weight": 1.0} for s in md["matched_skills"]],
                missing_skills=[{"skill": s, "weight": 1.0} for s in md["missing_skills"]],
                reasoning=md["reasoning"],
                pipeline_stage=md["pipeline_stage"],
            )
            db.add(match)
            await db.flush()
            created_matches.append(match)

        # ── 4. Create Evidence Records ────────────────────────────────
        for md in match_data:
            candidate = created_candidates[md["candidate_idx"]]
            for skill in md["matched_skills"]:
                evidence = Evidence(
                    candidate_id=candidate.id,
                    claim_type="skill_match",
                    claim_text=f"Candidate demonstrates proficiency in {skill}.",
                    verbatim_source_text=f"[From resume] ...experience with {skill} in production environments...",
                    source_type="resume",
                    confidence_score=0.90,
                )
                db.add(evidence)

        # ── 5. Create Completed Interview for Aisha ───────────────────
        interview = Interview(
            job_id=job.id,
            candidate_id=created_candidates[0].id,
            match_id=created_matches[0].id,
            created_by_user_id=current_user.id,
            status="completed",
            current_question_index=5,
            tamper_flag=False,
            started_at=utc_now(),
            completed_at=utc_now(),
        )
        db.add(interview)
        await db.flush()

        # Interview questions and answers
        qa_pairs = [
            {
                "category": "technical_depth",
                "question": "Describe your experience designing microservices architectures. What patterns do you use for inter-service communication?",
                "intent": "Assess distributed systems design competency",
                "answer": "I've designed event-driven microservices at CloudScale using Python/FastAPI with async message passing via AWS SQS and SNS. For synchronous calls we use gRPC with circuit breakers. I follow the saga pattern for distributed transactions and implement API gateways for external traffic. Each service owns its own PostgreSQL schema to maintain data isolation.",
            },
            {
                "category": "gap_probe",
                "question": "Your resume mentions AWS heavily but not GCP. How would you approach working in a multi-cloud environment?",
                "intent": "Probe cloud platform flexibility",
                "answer": "While I've primarily used AWS, the fundamental concepts transfer directly — compute, storage, networking, IAM. I've studied GCP's BigQuery and Cloud Run for a side project. I'd leverage Terraform for cloud-agnostic infrastructure-as-code, and I'm comfortable learning new platforms quickly given my strong foundations.",
            },
            {
                "category": "behavioral",
                "question": "Tell me about a time you had to mentor a struggling junior engineer. How did you approach it?",
                "intent": "Evaluate leadership and mentoring capability",
                "answer": "At CloudScale, I noticed a junior engineer was overwhelmed by a complex migration task. I broke the work into smaller tickets, pair-programmed the hardest parts, and set up daily 15-minute check-ins. Within 3 weeks they were independently shipping quality code. I also created an onboarding guide that reduced ramp-up time for new hires from 6 weeks to 3.",
            },
            {
                "category": "culture_fit",
                "question": "How do you handle disagreements about technical approaches with peers?",
                "intent": "Assess collaboration and conflict resolution",
                "answer": "I focus on data and outcomes rather than opinions. When I disagreed with a colleague about database choices, I proposed we each build a proof-of-concept with clear benchmarks. The data showed PostgreSQL with proper indexing outperformed the NoSQL alternative for our read-heavy workload. The key is keeping discussions professional and outcome-oriented.",
            },
            {
                "category": "situational",
                "question": "You discover a critical production bug at 5 PM on Friday. What's your incident response process?",
                "intent": "Evaluate incident management and reliability engineering",
                "answer": "First, I'd assess severity — is it data-corrupting or just degrading UX? For critical issues, I'd immediately page the on-call team, create an incident channel, and communicate status to stakeholders. I'd start with rollback if safe, then investigate root cause. After resolution, I'd lead a blameless postmortem to identify systemic improvements and update our runbooks.",
            },
        ]

        for idx, qa in enumerate(qa_pairs):
            q = InterviewQuestion(
                interview_id=interview.id,
                order_index=idx,
                category=qa["category"],
                question_text=qa["question"],
                intent=qa["intent"],
                rubric_criteria={
                    "correctness": "Demonstrates accurate technical knowledge",
                    "depth": "Provides specific examples and implementation details",
                    "communication": "Clear, structured, and concise response",
                },
            )
            db.add(q)
            await db.flush()

            a = InterviewAnswer(
                question_id=q.id,
                interview_id=interview.id,
                transcript_text=qa["answer"],
                attempt_number=1,
            )
            db.add(a)

        await db.flush()

        # ── 6. Create Evaluation ──────────────────────────────────────
        evaluation = Evaluation(
            interview_id=interview.id,
            match_id=created_matches[0].id,
            technical_score=91.0,
            communication_score=88.5,
            depth_score=89.0,
            overall_interview_score=89.7,
            category_scores={
                "technical_depth": 93.0,
                "gap_probe": 85.0,
                "behavioral": 90.0,
                "culture_fit": 88.0,
                "situational": 92.0,
            },
            strengths=[
                "Exceptional microservices architecture experience with production-scale systems",
                "Strong mentoring and leadership skills with measurable impact",
                "Data-driven decision making in technical disagreements",
                "Solid incident response methodology with blameless postmortem culture",
            ],
            weaknesses=[
                "Limited multi-cloud (GCP) direct experience — but shows strong learning agility",
            ],
            executive_summary=(
                "Aisha Patel completed the Senior Full-Stack Engineer screening interview with an "
                "overall score of 89.7%. Technical depth scored 91.0%, communication clarity scored "
                "88.5%, and problem-solving depth scored 89.0%. AI Recommendation: ADVANCE. "
                "Final hiring authority remains with the recruiter."
            ),
            ai_recommendation="advance",
        )
        db.add(evaluation)
        await db.flush()

        # ── 7. Create Audit Trail ─────────────────────────────────────
        audit_events = [
            ("job_created", "job", job.id, {"title": job.title}),
            ("candidate_created", "candidate", created_candidates[0].id, {"name": "Aisha Patel"}),
            ("candidate_created", "candidate", created_candidates[1].id, {"name": "Marcus Chen"}),
            ("candidate_created", "candidate", created_candidates[2].id, {"name": "Dr. Elena Rodriguez"}),
            ("match_analysis_completed", "match", created_matches[0].id, {"score": 92.5}),
            ("interview_prepared", "interview", interview.id, {"questions": 5}),
            ("interview_finalized", "interview", interview.id, {"status": "completed"}),
            ("evaluation_generated", "evaluation", evaluation.id, {"score": 89.7}),
        ]

        for action, entity_type, entity_id, details in audit_events:
            audit = AuditLog(
                org_id=org_id,
                user_id=current_user.id,
                action=action,
                entity_type=entity_type,
                entity_id=str(entity_id),
                details=details,
            )
            db.add(audit)

        await db.commit()

        return {
            "status": "success",
            "message": "Demo data seeded successfully.",
            "summary": {
                "jobs_created": 1,
                "candidates_created": len(created_candidates),
                "matches_created": len(created_matches),
                "interviews_created": 1,
                "evaluations_created": 1,
                "audit_events_created": len(audit_events),
            },
        }

    except Exception as exc:
        await db.rollback()
        logger.error("Demo seed failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demo seed failed: {str(exc)}",
        )
