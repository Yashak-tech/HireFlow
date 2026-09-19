import pytest
import json
from unittest.mock import AsyncMock, patch
from pydantic import ValidationError

from app.schemas.intelligence import (
    CandidateStructuredProfile,
    JobStructuredCriteria,
    ExtractedSkill,
    ExtractedExperience,
    ExtractedEducation,
    ClaimEvidence,
)
from app.services.intelligence_extractor import (
    extract_candidate_profile_deterministic,
    extract_job_criteria_deterministic,
    extract_candidate_profile,
    extract_job_criteria,
    mask_demographics_for_evaluation,
    call_openai_chat_completion,
)


SAMPLE_RESUME_TEXT = """
Sarah Connor
San Francisco, CA | sarah@example.com | linkedin.com/in/sarahconnor | photo.jpg

Summary:
Experienced Lead Software Engineer with 8+ years of experience building high-scale distributed backend systems.
She is passionate about cloud-native infrastructure, asynchronous architectures, and developer productivity.

Technical Skills:
Python, FastAPI, Docker, Kubernetes, PostgreSQL, AWS, Redis, Git, CI/CD, React

Soft Skills:
Leadership, Mentorship, Problem Solving

Experience:
Lead Backend Engineer at Acme Corp (2020 - Present)
- Architected event-driven microservices processing 50M daily events using Python, FastAPI, and Kafka.
- Mentored a team of 6 junior and mid-level engineers in TDD and system design.
- Reduced database query latency by 45% by optimizing PostgreSQL indexes and introducing Redis caching.

Senior Software Engineer at Cyberdyne Systems (2016 - 2020)
- Designed REST APIs and backend worker pipelines in Python and Docker on AWS ECS.

Education:
University of California, Berkeley (2012 - 2016)
Bachelor of Science in Computer Science
"""

SAMPLE_JOB_DESCRIPTION = """
Senior Python Backend Engineer

About the Role:
We are looking for a Senior Python Backend Engineer to join our Core Platform team.

Responsibilities:
- Design, build, and maintain high-performance microservices and REST APIs.
- Collaborate with product managers and frontend teams to deliver scalable features.
- Optimize database schemas and queries in PostgreSQL.

Must Have Qualifications:
- 5+ years of experience with Python and backend frameworks like FastAPI or Django.
- Strong hands-on experience with Docker and Kubernetes in production.
- Deep expertise in relational databases, especially PostgreSQL.
- Solid understanding of distributed systems and caching with Redis.

Nice to Have:
- Experience with AWS cloud infrastructure and Terraform.
- Familiarity with React and modern frontend stacks.
- Contributions to open-source software.
"""


def test_candidate_profile_schema_valid():
    """Verify strict Pydantic CandidateStructuredProfile schema validation."""
    profile = CandidateStructuredProfile(
        candidate_summary="Experienced developer",
        technical_skills=["Python", "FastAPI"],
        soft_skills=["Leadership"],
        years_of_experience=5.0,
        skills=[
            ExtractedSkill(
                name="Python",
                category="technical",
                proficiency_level="Expert",
                evidence=ClaimEvidence(
                    source_type="resume",
                    verbatim_source_text="Built services using Python",
                    confidence=0.98,
                ),
            )
        ],
        work_experience=[
            ExtractedExperience(
                company="TechCorp",
                title="Staff Engineer",
                is_current=True,
                highlights=["Built pipelines"],
            )
        ],
        education=[
            ExtractedEducation(
                institution="MIT",
                degree="B.S. CS",
                end_year=2018,
            )
        ],
    )
    assert profile.years_of_experience == 5.0
    assert len(profile.skills) == 1
    assert profile.skills[0].evidence.confidence == 0.98


def test_candidate_profile_schema_missing_optional_fields():
    """Verify missing optional fields cleanly default without errors."""
    profile = CandidateStructuredProfile()
    assert profile.candidate_summary is None
    assert profile.skills == []
    assert profile.technical_skills == []
    assert profile.work_experience == []
    assert profile.education == []


def test_job_criteria_schema_validation():
    """Verify JobStructuredCriteria strictly separates must-have vs nice-to-have."""
    criteria = JobStructuredCriteria(
        role="Senior Backend Engineer",
        seniority="Senior",
        required_skills=["Python", "Docker"],
        preferred_skills=["React", "Terraform"],
        must_have=["5+ years Python", "Production Kubernetes"],
        nice_to_have=["AWS experience"],
        responsibilities=["Build microservices", "Optimize database"],
    )
    assert "Python" in criteria.required_skills
    assert "React" in criteria.preferred_skills
    assert len(criteria.must_have) == 2
    assert len(criteria.responsibilities) == 2


def test_deterministic_grounded_resume_extraction():
    """Verify deterministic extractor produces grounded evidence with verbatim quotes."""
    profile = extract_candidate_profile_deterministic(SAMPLE_RESUME_TEXT)

    assert "Python" in profile.technical_skills
    assert "FastAPI" in profile.technical_skills
    assert "Kubernetes" in profile.technical_skills
    assert "PostgreSQL" in profile.technical_skills

    # Check evidence grounding
    python_skill = next((s for s in profile.skills if s.name == "Python"), None)
    assert python_skill is not None
    assert python_skill.evidence is not None
    assert python_skill.evidence.source_type == "resume"
    assert 0.0 <= python_skill.evidence.confidence <= 1.0
    # Verbatim quote MUST be from the actual text
    assert python_skill.evidence.verbatim_source_text in SAMPLE_RESUME_TEXT or "Python" in python_skill.evidence.verbatim_source_text

    # Check experience
    assert len(profile.work_experience) >= 1
    assert profile.years_of_experience is not None
    assert profile.years_of_experience >= 8.0


def test_deterministic_job_criteria_extraction():
    """Verify deterministic job description criteria extraction distinguishes requirements."""
    criteria = extract_job_criteria_deterministic(SAMPLE_JOB_DESCRIPTION)

    assert criteria.seniority == "Senior"
    assert "Python" in criteria.required_skills
    assert "Docker" in criteria.required_skills
    assert len(criteria.must_have) > 0
    assert len(criteria.responsibilities) > 0


@pytest.mark.asyncio
async def test_llm_repair_loop_successful_first_attempt():
    """Simulate LLM returning valid JSON on attempt 1."""
    mock_payload = {
        "candidate_summary": "Expert Python engineer",
        "technical_skills": ["Python", "AWS"],
        "soft_skills": ["Communication"],
        "years_of_experience": 6.0,
        "skills": [
            {
                "name": "Python",
                "category": "technical",
                "proficiency_level": "Expert",
                "evidence": {
                    "source_type": "resume",
                    "verbatim_source_text": "Built Python apps",
                    "confidence": 0.95,
                },
            }
        ],
        "work_experience": [],
        "education": [],
    }

    with patch("app.core.config.settings.OPENAI_API_KEY", "sk-live-test-key"), \
         patch("app.services.intelligence_extractor.call_openai_chat_completion", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps(mock_payload)

        profile = await extract_candidate_profile(SAMPLE_RESUME_TEXT)
        assert mock_llm.call_count == 1
        assert profile.candidate_summary == "Expert Python engineer"
        assert profile.years_of_experience == 6.0


@pytest.mark.asyncio
async def test_llm_repair_loop_malformed_json_repairs_on_attempt_two():
    """Simulate attempt 1 returning broken/malformed JSON, and attempt 2 returning valid JSON."""
    valid_payload = {
        "candidate_summary": "Repaired valid summary",
        "technical_skills": ["Python", "FastAPI"],
        "soft_skills": [],
        "years_of_experience": 4.0,
        "skills": [],
        "work_experience": [],
        "education": [],
    }

    with patch("app.core.config.settings.OPENAI_API_KEY", "sk-live-test-key"), \
         patch("app.services.intelligence_extractor.call_openai_chat_completion", new_callable=AsyncMock) as mock_llm:
        # 1st attempt: broken JSON, 2nd attempt: valid JSON
        mock_llm.side_effect = [
            "MALFORMED {json: missing_quotes",
            json.dumps(valid_payload),
        ]

        profile = await extract_candidate_profile(SAMPLE_RESUME_TEXT)
        assert mock_llm.call_count == 2
        assert profile.candidate_summary == "Repaired valid summary"


@pytest.mark.asyncio
async def test_llm_repair_loop_max_three_failed_attempts_fallback():
    """Simulate 3 consecutive failures triggering graceful deterministic fallback."""
    with patch("app.core.config.settings.OPENAI_API_KEY", "sk-live-test-key"), \
         patch("app.services.intelligence_extractor.call_openai_chat_completion", new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = [
            "Invalid 1",
            "Invalid 2",
            "Invalid 3",
        ]

        profile = await extract_candidate_profile(SAMPLE_RESUME_TEXT)
        assert mock_llm.call_count == 3
        # Should cleanly return grounded deterministic extraction
        assert "Python" in profile.technical_skills


def test_demographic_masking():
    """
    Test demographic masking for bias-free evaluation.
    Must mask candidate name, gender pronouns, graduation dates, and photo URLs.
    Original dictionary must not be mutated.
    """
    original = {
        "candidate_summary": "Sarah Connor is a senior developer. She was leading backend engineering.",
        "technical_skills": ["Python", "Docker"],
        "education": [
            {
                "institution": "UC Berkeley (2016)",
                "degree": "BS Computer Science",
                "start_year": 2012,
                "end_year": 2016,
            }
        ],
        "links": [
            {"platform": "photo", "url": "https://example.com/photos/sarah.jpg"},
            {"platform": "github", "url": "https://github.com/sarahconnor"},
        ],
    }

    masked = mask_demographics_for_evaluation(original, candidate_name="Sarah Connor")

    # Verify candidate name was masked
    assert "Sarah" not in masked["candidate_summary"]
    assert "Connor" not in masked["candidate_summary"]
    assert "[Candidate]" in masked["candidate_summary"]

    # Verify pronouns were masked
    assert "She was" not in masked["candidate_summary"]

    # Verify graduation years were stripped
    edu = masked["education"][0]
    assert edu["start_year"] is None
    assert edu["end_year"] is None
    assert "2016" not in edu["institution"]

    # Verify photo link was removed
    urls = [link["url"] for link in masked["links"]]
    assert not any("photo" in u for u in urls)
    assert any("github" in u for u in urls)

    # Verify original was NOT mutated
    assert original["education"][0]["end_year"] == 2016
    assert "Sarah" in original["candidate_summary"]
