import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.embeddings import (
    generate_deterministic_embedding,
    generate_embedding,
    cosine_similarity,
    EMBEDDING_DIM,
)
from app.services.matching_engine import (
    evaluate_candidate_match,
    find_skill_evidence,
    extract_required_years_from_job,
)
from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.models.candidate import Candidate
from app.models.candidate_skill import CandidateSkill
from app.models.evidence import Evidence
from app.models.resume import Resume


async def get_auth_token(client: AsyncClient, persona: str = "sarah_jenkins") -> str:
    login_resp = await client.post("/api/auth/demo-login", json={"persona": persona})
    return login_resp.json()["access_token"]


# =========================================================================
# 1. EMBEDDINGS & VECTOR SIMILARITY TESTS
# =========================================================================

def test_deterministic_embedding_dimension_and_norm():
    """Verify deterministic vector has exact 1536 dims and unit L2 norm."""
    vec = generate_deterministic_embedding("Python FastAPI PostgreSQL Backend Developer")
    assert len(vec) == EMBEDDING_DIM
    # Check L2 norm is 1.0 (within float precision)
    norm = sum(x * x for x in vec) ** 0.5
    assert abs(norm - 1.0) < 1e-3


def test_identical_texts_cosine_similarity_is_one():
    """Identical texts must produce cosine similarity of 1.0."""
    t1 = "Senior Python Developer with AWS, Docker, Kubernetes"
    vec1 = generate_deterministic_embedding(t1)
    vec2 = generate_deterministic_embedding(t1)
    sim = cosine_similarity(vec1, vec2)
    assert abs(sim - 1.0) < 1e-3


def test_domain_differentiation_cosine_similarity():
    """
    Overlapping tech stacks (Python, FastAPI, Postgres) must yield significantly higher
    similarity than orthogonal domains (React, Tailwind, HTML vs Python Backend).
    """
    target_job = "Python, FastAPI, PostgreSQL, Docker, AWS backend engineer"
    candidate_aligned = "Python, FastAPI, PostgreSQL, Redis, Docker, cloud deployment"
    candidate_unrelated = "Frontend React, HTML, CSS, Figma design, UI/UX styling"

    vec_job = generate_deterministic_embedding(target_job)
    vec_aligned = generate_deterministic_embedding(candidate_aligned)
    vec_unrelated = generate_deterministic_embedding(candidate_unrelated)

    sim_aligned = cosine_similarity(vec_job, vec_aligned)
    sim_unrelated = cosine_similarity(vec_job, vec_unrelated)

    assert sim_aligned > 0.50, f"Expected high similarity for aligned stack, got {sim_aligned}"
    assert sim_unrelated < 0.35, f"Expected low similarity for unrelated stack, got {sim_unrelated}"
    assert sim_aligned > (sim_unrelated + 0.20)


def test_empty_and_whitespace_embedding():
    """Empty or whitespace text must return a valid unit vector without throwing."""
    vec_empty = generate_deterministic_embedding("")
    vec_spaces = generate_deterministic_embedding("   \n\t  ")
    assert len(vec_empty) == EMBEDDING_DIM
    assert len(vec_spaces) == EMBEDDING_DIM
    norm_empty = sum(x * x for x in vec_empty) ** 0.5
    assert abs(norm_empty - 1.0) < 1e-3


def test_cosine_similarity_edge_cases():
    """Check None and dimension mismatch handling."""
    assert cosine_similarity(None, [1.0, 2.0]) == 0.0
    assert cosine_similarity([1.0, 2.0], None) == 0.0
    assert cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0]) == 0.0
    assert cosine_similarity([0.0, 0.0], [0.0, 0.0]) == 0.0


# =========================================================================
# 2. MATCHING ENGINE CORE UNIT TESTS
# =========================================================================

def test_find_skill_evidence_grounding():
    """Verify evidence retrieval citations and missing requirements."""
    cand = Candidate(id="c1", org_id="o1", full_name="Jane Doe", email="jane@test.com")
    skills = [
        CandidateSkill(candidate_id="c1", skill_name="Python"),
        CandidateSkill(candidate_id="c1", skill_name="PostgreSQL"),
    ]
    evidence_items = [
        Evidence(
            candidate_id="c1",
            claim_type="skill",
            claim_text="Python",
            verbatim_source_text="Built scalable REST APIs using Python and FastAPI framework.",
            confidence_score=0.95,
        )
    ]
    raw_text = "Experienced software engineer with 5 years in Python and PostgreSQL database architecture."

    # Matched via grounded Evidence
    status, quote, conf = find_skill_evidence("Python", cand, skills, evidence_items, raw_text)
    assert status == "MATCHED"
    assert "FastAPI" in quote
    assert conf >= 0.90

    # Matched via CandidateSkill / raw resume text
    status2, quote2, conf2 = find_skill_evidence("PostgreSQL", cand, skills, evidence_items, raw_text)
    assert status2 == "MATCHED"
    assert "PostgreSQL" in quote2

    # Missing requirement
    status3, quote3, conf3 = find_skill_evidence("Kubernetes", cand, skills, evidence_items, raw_text)
    assert status3 == "MISSING"
    assert "No explicit Kubernetes experience found in candidate evidence" in quote3
    assert conf3 == 0.0


@pytest.mark.asyncio
async def test_evaluate_candidate_match_perfect_fit():
    """Candidate with all required skills and experience >= required gets high match score."""
    job = Job(
        id="j1",
        org_id="o1",
        created_by_user_id="u1",
        title="Senior Python Backend Engineer",
        department="Engineering",
        raw_description="Looking for Senior Python Developer with 4+ years of experience in Python, FastAPI, and PostgreSQL.",
        parsed_criteria={"experience_years_required": 4.0},
    )
    reqs = [
        JobRequirement(id="r1", job_id="j1", requirement_text="Python", requirement_type="must_have", weight=1.2),
        JobRequirement(id="r2", job_id="j1", requirement_text="FastAPI", requirement_type="must_have", weight=1.2),
        JobRequirement(id="r3", job_id="j1", requirement_text="PostgreSQL", requirement_type="must_have", weight=1.0),
    ]

    cand = Candidate(
        id="c1",
        org_id="o1",
        full_name="Rahul Sharma",
        email="rahul@example.com",
        years_of_experience=5.0,
    )
    skills = [
        CandidateSkill(candidate_id="c1", skill_name="Python"),
        CandidateSkill(candidate_id="c1", skill_name="FastAPI"),
        CandidateSkill(candidate_id="c1", skill_name="PostgreSQL"),
    ]
    evidence_items = [
        Evidence(candidate_id="c1", claim_type="skill", claim_text="Python", verbatim_source_text="Over 5 years building Python microservices.", confidence_score=0.95),
        Evidence(candidate_id="c1", claim_type="skill", claim_text="FastAPI", verbatim_source_text="Implemented high performance FastAPI endpoints.", confidence_score=0.95),
        Evidence(candidate_id="c1", claim_type="skill", claim_text="PostgreSQL", verbatim_source_text="Designed and optimized PostgreSQL relational schemas.", confidence_score=0.95),
    ]
    resumes = [
        Resume(
            candidate_id="c1",
            file_name="rahul_resume.pdf",
            file_path="uploads/rahul.pdf",
            file_type="pdf",
            file_size_bytes=1024,
            raw_text="Rahul Sharma. Senior Python developer with 5 years experience in FastAPI and PostgreSQL.",
            parsing_status="completed",
        )
    ]

    eval_res = await evaluate_candidate_match(job, cand, reqs, skills, evidence_items, resumes)

    assert eval_res["skill_overlap_score"] == 100.0
    assert eval_res["experience_fit_score"] == 100.0
    assert eval_res["vector_similarity"] > 0.60
    assert eval_res["overall_match_score"] > 85.0
    assert len(eval_res["matched_skills"]) == 3
    assert len(eval_res["missing_skills"]) == 0
    assert "Python" in eval_res["reasoning"]


@pytest.mark.asyncio
async def test_evaluate_candidate_match_unrelated_candidate():
    """Unrelated candidate (React frontend) against Python Backend job gets low match score."""
    job = Job(
        id="j1",
        org_id="o1",
        created_by_user_id="u1",
        title="Senior Python Backend Engineer",
        department="Engineering",
        raw_description="Looking for Senior Python Developer with 4+ years of experience in Python, FastAPI, and PostgreSQL.",
        parsed_criteria={"experience_years_required": 4.0},
    )
    reqs = [
        JobRequirement(id="r1", job_id="j1", requirement_text="Python", requirement_type="must_have", weight=1.2),
        JobRequirement(id="r2", job_id="j1", requirement_text="FastAPI", requirement_type="must_have", weight=1.2),
        JobRequirement(id="r3", job_id="j1", requirement_text="PostgreSQL", requirement_type="must_have", weight=1.0),
    ]

    cand = Candidate(
        id="c2",
        org_id="o1",
        full_name="Amit Kumar",
        email="amit@example.com",
        years_of_experience=2.0,
    )
    skills = [
        CandidateSkill(candidate_id="c2", skill_name="React"),
        CandidateSkill(candidate_id="c2", skill_name="JavaScript"),
        CandidateSkill(candidate_id="c2", skill_name="CSS"),
    ]
    evidence_items = [
        Evidence(candidate_id="c2", claim_type="skill", claim_text="React", verbatim_source_text="Built responsive web UIs using React and CSS.", confidence_score=0.95),
    ]
    resumes = [
        Resume(
            candidate_id="c2",
            file_name="amit_resume.pdf",
            file_path="uploads/amit.pdf",
            file_type="pdf",
            file_size_bytes=1024,
            raw_text="Amit Kumar. Frontend developer with 2 years experience in React, JavaScript, HTML, CSS.",
            parsing_status="completed",
        )
    ]

    eval_res = await evaluate_candidate_match(job, cand, reqs, skills, evidence_items, resumes)

    assert eval_res["skill_overlap_score"] == 0.0
    assert eval_res["experience_fit_score"] == 50.0  # 2 yrs / 4 yrs = 50%
    assert eval_res["vector_similarity"] < 0.35
    assert eval_res["overall_match_score"] < 40.0
    assert len(eval_res["matched_skills"]) == 0
    assert len(eval_res["missing_skills"]) == 3
    # Verify exact missing skill quote format
    assert "No explicit Python experience found in candidate evidence" in eval_res["missing_skills"][0]["reason"]


# =========================================================================
# 3. END-TO-END MATCHING API INTEGRATION TESTS
# =========================================================================

@pytest.mark.asyncio
async def test_matching_api_full_flow():
    """
    Test complete Phase 4 API workflow:
    1. Create Job with requirements
    2. Create aligned Candidate A and unrelated Candidate B
    3. Run POST /api/matching/{job_id}/run
    4. Verify MatchRunResponse with rankings: Candidate A ranked > Candidate B
    5. Verify CandidateMatch record pipeline_stage transitioned to 'evaluated'
    6. Verify GET /api/matching/{job_id}/results
    7. Verify GET /api/matching/{job_id}/candidate/{candidate_id}
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        token = await get_auth_token(ac, "sarah_jenkins")
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create Job with requirements
        job_resp = await ac.post(
            "/api/jobs",
            headers=headers,
            json={
                "title": "AI Backend Engineer",
                "department": "Engineering",
                "raw_description": "Seeking AI Backend Engineer with 3+ years experience in Python, FastAPI, and PostgreSQL.",
                "requirements": [
                    {"requirement_text": "Python", "requirement_type": "must_have", "category": "skill", "weight": 1.2},
                    {"requirement_text": "FastAPI", "requirement_type": "must_have", "category": "skill", "weight": 1.2},
                    {"requirement_text": "PostgreSQL", "requirement_type": "must_have", "category": "skill", "weight": 1.0},
                ],
            },
        )
        assert job_resp.status_code == 201
        job_id = job_resp.json()["id"]

        # 2. Create Candidate A (aligned)
        cand_a_resp = await ac.post(
            "/api/candidates",
            headers=headers,
            json={
                "full_name": "Candidate A (Aligned)",
                "email": "cand.a@example.com",
                "years_of_experience": 4.0,
                "skills": [
                    {"skill_name": "Python"},
                    {"skill_name": "FastAPI"},
                    {"skill_name": "PostgreSQL"},
                    {"skill_name": "Docker"},
                ],
            },
        )
        assert cand_a_resp.status_code == 201
        cand_a_id = cand_a_resp.json()["id"]

        # Associate Candidate A with Job
        assoc_a = await ac.post(f"/api/candidates/{cand_a_id}/associate-job/{job_id}", headers=headers)
        assert assoc_a.status_code == 200

        # 3. Create Candidate B (unrelated)
        cand_b_resp = await ac.post(
            "/api/candidates",
            headers=headers,
            json={
                "full_name": "Candidate B (Frontend)",
                "email": "cand.b@example.com",
                "years_of_experience": 1.0,
                "skills": [
                    {"skill_name": "React"},
                    {"skill_name": "CSS"},
                    {"skill_name": "HTML"},
                ],
            },
        )
        assert cand_b_resp.status_code == 201
        cand_b_id = cand_b_resp.json()["id"]

        # Associate Candidate B with Job
        assoc_b = await ac.post(f"/api/candidates/{cand_b_id}/associate-job/{job_id}", headers=headers)
        assert assoc_b.status_code == 200

        # 4. Run Matching: POST /api/matching/{job_id}/run
        run_resp = await ac.post(f"/api/matching/{job_id}/run", headers=headers)
        assert run_resp.status_code == 200
        run_data = run_resp.json()

        assert run_data["job_id"] == job_id
        assert run_data["total_candidates_evaluated"] == 2
        matches = run_data["matches"]

        # Rank 1 must be Candidate A with higher score
        assert matches[0]["candidate_id"] == cand_a_id
        assert matches[0]["overall_match_score"] > matches[1]["overall_match_score"]
        assert matches[0]["pipeline_stage"] == "evaluated"
        assert matches[0]["skill_overlap_score"] == 100.0

        # Candidate B must have missing skills identified
        assert matches[1]["candidate_id"] == cand_b_id
        assert matches[1]["skill_overlap_score"] == 0.0
        assert len(matches[1]["missing_skills"]) >= 3

        # 5. Verify GET /api/matching/{job_id}/results
        results_resp = await ac.get(f"/api/matching/{job_id}/results", headers=headers)
        assert results_resp.status_code == 200
        results_data = results_resp.json()
        assert len(results_data) == 2
        assert results_data[0]["candidate_id"] == cand_a_id

        # 6. Verify GET /api/matching/{job_id}/candidate/{candidate_id}
        detail_resp = await ac.get(f"/api/matching/{job_id}/candidate/{cand_a_id}", headers=headers)
        assert detail_resp.status_code == 200
        detail_data = detail_resp.json()
        assert detail_data["candidate_id"] == cand_a_id
        assert len(detail_data["requirements_breakdown"]) == 3
        for item in detail_data["requirements_breakdown"]:
            assert item["status"] == "MATCHED"


@pytest.mark.asyncio
async def test_matching_tenant_isolation():
    """Verify cross-tenant security: Org A cannot run matching on Org B's jobs."""
    from tests.test_candidates import create_secondary_org_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        token_sarah = await get_auth_token(ac, "sarah_jenkins")
        _, _, other_org_token = await create_secondary_org_user()

        # Sarah creates job in her Org
        job_resp = await ac.post(
            "/api/jobs",
            headers={"Authorization": f"Bearer {token_sarah}"},
            json={
                "title": "Sarah Internal Role",
                "department": "Engineering",
                "raw_description": "Role in Sarah Org",
            },
        )
        job_id = job_resp.json()["id"]

        # Recruiter from other org attempts to run matching on Sarah's job -> 404
        bad_run = await ac.post(
            f"/api/matching/{job_id}/run",
            headers={"Authorization": f"Bearer {other_org_token}"},
        )
        assert bad_run.status_code == 404

        # Recruiter from other org attempts to view results -> 404
        bad_get = await ac.get(
            f"/api/matching/{job_id}/results",
            headers={"Authorization": f"Bearer {other_org_token}"},
        )
        assert bad_get.status_code == 404


@pytest.mark.asyncio
async def test_matching_unauthenticated_rejected():
    """Unauthenticated requests to matching endpoints must return 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/matching/fake-id/run")
        assert resp.status_code == 401
