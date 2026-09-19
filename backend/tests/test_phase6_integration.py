"""
Integration tests for Phase 6: Product Integration, Multi-Source Evidence, Audit Trails,
Interview Evaluation, Human-in-the-Loop Decision Governance, and NL Candidate Query.
"""
import io
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


async def get_auth_token(client: AsyncClient, persona: str = "sarah_jenkins") -> str:
    login_resp = await client.post("/api/auth/demo-login", json={"persona": persona})
    return login_resp.json()["access_token"]


SAMPLE_RESUME = """
Marcus Vance
Senior Backend Engineer | marcus.vance@ai-labs.demo | New York, NY

Summary:
Senior Backend Engineer with 5+ years building scalable distributed microservices with Python, FastAPI, and PostgreSQL.

Skills:
Python, FastAPI, PostgreSQL, Redis, Docker, Git, REST APIs, Microservices, AWS

Experience:
Senior Software Engineer at CloudScale Inc (2020 - Present)
- Designed and maintained async FastAPI services with PostgreSQL and Redis handling 50k req/min.
- Containerized microservices using Docker and orchestrated deployments on AWS ECS.

Software Engineer at TechCorp (2018 - 2020)
- Developed RESTful APIs using Python and PostgreSQL.

Education:
B.S. in Computer Science, Columbia University (2014 - 2018)
"""


@pytest.mark.asyncio
async def test_phase6_end_to_end_recruiter_workflow():
    """
    Test complete Phase 6 end-to-end flow:
    Job -> Candidate -> Resume -> Match -> Interview -> Evaluation -> Multi-Source Evidence -> Human Recruiter Decision -> Audit Trail.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await get_auth_token(client, "sarah_jenkins")
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 1. Create Job
        job_res = await client.post(
            "/api/jobs",
            headers=auth_headers,
            json={
                "title": "Senior AI Backend Engineer",
                "department": "AI Engineering",
                "raw_description": "We are seeking a Senior AI Backend Engineer with Python, FastAPI, PostgreSQL, Docker, AWS, and OpenAI APIs.",
                "requirements": [
                    {"requirement_text": "Python", "requirement_type": "must_have", "category": "skill"},
                    {"requirement_text": "FastAPI", "requirement_type": "must_have", "category": "skill"},
                    {"requirement_text": "PostgreSQL", "requirement_type": "must_have", "category": "skill"},
                ],
            },
        )
        assert job_res.status_code == 201
        job_id = job_res.json()["id"]

        # 2. Parse JD
        jd_res = await client.post(f"/api/jobs/{job_id}/parse-jd", headers=auth_headers)
        assert jd_res.status_code == 200

        # 3. Create Candidate
        cand_res = await client.post(
            "/api/candidates",
            headers=auth_headers,
            json={
                "full_name": "Marcus Vance",
                "email": "marcus.vance@ai-labs.demo",
                "current_title": "Backend Software Engineer",
                "current_company": "CloudScale Inc",
                "years_of_experience": 5.0,
                "job_id": job_id,
            },
        )
        assert cand_res.status_code == 201
        cand_id = cand_res.json()["id"]

        # 4. Upload & Parse Resume
        upload_resp = await client.post(
            f"/api/candidates/{cand_id}/resume",
            headers=auth_headers,
            files={"file": ("marcus_resume.txt", io.BytesIO(SAMPLE_RESUME.encode("utf-8")), "text/plain")},
        )
        assert upload_resp.status_code == 200

        parse_res = await client.post(
            f"/api/candidates/{cand_id}/parse-resume",
            headers=auth_headers,
        )
        assert parse_res.status_code == 200

        # 5. Check Initial Resume Evidence
        evidence_res1 = await client.get(f"/api/candidates/{cand_id}/evidence", headers=auth_headers)
        assert evidence_res1.status_code == 200
        ev_items1 = evidence_res1.json()
        assert len(ev_items1) > 0
        assert all(ev["source_type"] == "resume" for ev in ev_items1)

        # 6. Run Matching Analysis
        match_res = await client.post(f"/api/matching/{job_id}/run", headers=auth_headers)
        assert match_res.status_code == 200
        matches = match_res.json()["matches"]
        cand_match = next((m for m in matches if m["candidate_id"] == cand_id), None)
        assert cand_match is not None
        match_id = cand_match["match_id"]

        # 7. Prepare Interview
        prep_res = await client.post(
            "/api/interviews/prepare",
            headers=auth_headers,
            json={"job_id": job_id, "candidate_id": cand_id, "match_id": match_id},
        )
        assert prep_res.status_code == 200
        interview_id = prep_res.json()["interview"]["id"]
        total_questions = len(prep_res.json()["interview"]["questions"])

        # 8. Conduct Adaptive Interview Turns
        for i in range(total_questions):
            turn_res = await client.post(
                f"/api/interviews/{interview_id}/turn",
                headers=auth_headers,
                json={
                    "candidate_input": (
                        f"Detailed response for question {i+1}: In our microservices architecture, "
                        "I designed asynchronous FastAPI services utilizing SQLAlchemy 2.0 with connection pooling and asyncpg. "
                        "We implemented Redis caching to reduce database read latencies by 65%."
                    )
                },
            )
            assert turn_res.status_code == 200

        # 9. Finalize Interview & Verify Evaluation
        finalize_res = await client.post(f"/api/interviews/{interview_id}/finalize", headers=auth_headers)
        assert finalize_res.status_code == 200
        eval_data = finalize_res.json()
        assert eval_data["interview_id"] == interview_id
        assert eval_data["technical_score"] > 0
        assert eval_data["overall_interview_score"] > 0
        assert len(eval_data["strengths"]) > 0
        assert eval_data["ai_recommendation"] in ("advance", "review_needed", "reject")

        # 10. Verify Multi-Source Grounded Evidence (Resume + Interview)
        evidence_res2 = await client.get(f"/api/candidates/{cand_id}/evidence", headers=auth_headers)
        assert evidence_res2.status_code == 200
        ev_items2 = evidence_res2.json()
        sources = {ev["source_type"] for ev in ev_items2}
        assert "resume" in sources
        assert "interview" in sources

        # 11. Recruiter Makes Final Human Decision
        decision_res = await client.post(
            f"/api/interviews/{interview_id}/evaluation/decision",
            headers=auth_headers,
            json={
                "decision": "offer_extended",
                "notes": "Candidate demonstrated exceptional async database design and clear communication during screening.",
            },
        )
        assert decision_res.status_code == 200
        dec_data = decision_res.json()
        assert dec_data["human_decision"] == "offer_extended"
        assert "exceptional async database design" in dec_data["human_decision_notes"]

        # 12. Verify Audit Trail Records
        audit_res = await client.get("/api/audit", headers=auth_headers)
        assert audit_res.status_code == 200
        audit_logs = audit_res.json()
        actions = [log["action"] for log in audit_logs]
        assert "interview_finalized" in actions or "evaluation_generated" in actions
        assert "recruiter_decision" in actions


@pytest.mark.asyncio
async def test_phase6_natural_language_candidate_query():
    """
    Test lightweight natural-language query against candidate pool.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await get_auth_token(client, "sarah_jenkins")
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Create candidate with Python and FastAPI skills
        c1 = await client.post(
            "/api/candidates",
            headers=auth_headers,
            json={
                "full_name": "Devin Pythonic",
                "email": "devin.py@example.demo",
                "current_title": "Python Specialist",
                "years_of_experience": 4.0,
                "skills": [
                    {"skill_name": "Python", "category": "technical", "years_experience": 4.0},
                    {"skill_name": "FastAPI", "category": "framework", "years_experience": 3.0},
                    {"skill_name": "PostgreSQL", "category": "tool", "years_experience": 4.0},
                ],
            },
        )
        assert c1.status_code == 201

        # Create unrelated candidate
        c2 = await client.post(
            "/api/candidates",
            headers=auth_headers,
            json={
                "full_name": "Frontend Fiona",
                "email": "fiona.fe@example.demo",
                "current_title": "UI Designer",
                "years_of_experience": 1.0,
                "skills": [
                    {"skill_name": "Figma", "category": "tool", "years_experience": 1.0},
                    {"skill_name": "CSS", "category": "technical", "years_experience": 1.0},
                ],
            },
        )
        assert c2.status_code == 201

        # Run NL Query
        query_res = await client.post(
            "/api/candidates/query",
            headers=auth_headers,
            json={"query": "Find candidates with Python and FastAPI with at least 2 years experience"},
        )
        assert query_res.status_code == 200
        qdata = query_res.json()
        assert "python" in [s.lower() for s in qdata["parsed_skills"]]
        assert qdata["parsed_min_experience"] == 2.0
        assert len(qdata["results"]) > 0
        top_match = qdata["results"][0]
        assert top_match["candidate"]["full_name"] == "Devin Pythonic"
        assert top_match["match_score"] >= 90.0
        assert "Python" in top_match["reasoning"]
