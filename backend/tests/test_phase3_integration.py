import io
import pytest
from httpx import AsyncClient, ASGITransport
from pypdf import PdfWriter

from app.main import app


async def get_auth_token(client: AsyncClient, persona: str = "sarah_jenkins") -> str:
    login_resp = await client.post("/api/auth/demo-login", json={"persona": persona})
    return login_resp.json()["access_token"]

SAMPLE_RESUME_CONTENT = """
Alex Morgan
Senior Cloud Engineer | alex.morgan@example.com | San Francisco, CA

Professional Summary:
Lead Systems Architect with 7 years of experience deploying mission-critical infrastructure on AWS.
Specializes in Kubernetes, Docker, Python, PostgreSQL, and Terraform.

Core Skills:
Python, Docker, Kubernetes, AWS, PostgreSQL, Redis, Terraform, CI/CD, Leadership

Professional Experience:
Senior Platform Architect at CloudScale (2021 - Present)
- Automated Kubernetes cluster provisioning on AWS with Terraform and GitOps.
- Wrote high-throughput data processing services in Python and FastAPI.
- Tuned PostgreSQL queries and connection pooling for 25k concurrent users.

DevOps Engineer at InfraTech (2018 - 2021)
- Managed Dockerized microservices and automated CI/CD deployment pipelines.

Education:
University of Washington
Bachelor of Science in Computer Science (2014 - 2018)
"""


@pytest.mark.asyncio
async def test_parse_resume_full_lifecycle_and_evidence():
    """
    Test full Phase 3 resume parsing workflow:
    1. Upload resume
    2. Trigger parsing (pending -> processing -> completed)
    3. Verify candidate skills and parsed_profile
    4. Verify grounded evidence provenance
    5. Verify demographic masked profile
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        token = await get_auth_token(ac, "sarah_jenkins")
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create candidate
        create_resp = await ac.post(
            "/api/candidates",
            headers=headers,
            json={
                "full_name": "Alex Morgan",
                "email": "alex.morgan@testdomain.com",
                "phone": "+1-555-0199",
                "location": "San Francisco, CA",
            },
        )
        assert create_resp.status_code == 201
        candidate_id = create_resp.json()["id"]

        # 2. Upload text resume
        upload_resp = await ac.post(
            f"/api/candidates/{candidate_id}/resume",
            headers=headers,
            files={"file": ("alex_resume.txt", io.BytesIO(SAMPLE_RESUME_CONTENT.encode("utf-8")), "text/plain")},
        )
        assert upload_resp.status_code == 200
        candidate_data = upload_resp.json()
        assert len(candidate_data["resumes"]) == 1
        resume_id = candidate_data["resumes"][0]["id"]
        assert candidate_data["resumes"][0]["parsing_status"] == "pending"

        # 3. Trigger Phase 3 document intelligence parsing
        parse_resp = await ac.post(
            f"/api/candidates/{candidate_id}/parse-resume",
            headers=headers,
        )
        assert parse_resp.status_code == 200
        parse_result = parse_resp.json()
        assert parse_result["parsing_status"] == "completed"
        assert parse_result["skills_extracted_count"] > 0
        assert parse_result["evidence_items_count"] > 0
        assert "Python" in parse_result["parsed_profile"]["technical_skills"]

        # 4. Fetch candidate details and verify skills synchronized
        detail_resp = await ac.get(f"/api/candidates/{candidate_id}", headers=headers)
        assert detail_resp.status_code == 200
        skills = [s["skill_name"] for s in detail_resp.json()["skills"]]
        assert "Python" in skills
        assert "Kubernetes" in skills

        # 5. Fetch grounded evidence and verify provenance
        evidence_resp = await ac.get(f"/api/candidates/{candidate_id}/evidence", headers=headers)
        assert evidence_resp.status_code == 200
        evidence_list = evidence_resp.json()
        assert len(evidence_list) >= 3
        # Check Python evidence
        py_evidence = next((e for e in evidence_list if e["claim_text"] == "Python"), None)
        assert py_evidence is not None
        assert py_evidence["source_type"] == "resume"
        assert "Python" in py_evidence["verbatim_source_text"]
        assert 0.0 <= py_evidence["confidence_score"] <= 1.0

        # 6. Fetch demographic masked profile
        masked_resp = await ac.get(f"/api/candidates/{candidate_id}/masked-profile", headers=headers)
        assert masked_resp.status_code == 200
        anonymized = masked_resp.json()["anonymized_profile"]
        assert "Alex" not in (anonymized.get("candidate_summary") or "")
        assert "Morgan" not in (anonymized.get("candidate_summary") or "")


@pytest.mark.asyncio
async def test_parse_scanned_unreadable_pdf_fails_gracefully():
    """
    Test uploading a scanned / image-only blank PDF.
    Must transition parsing_status to 'failed' and return HTTP 422:
    'Unreadable PDF: Please provide a text-based PDF or DOCX format.'
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        token = await get_auth_token(ac, "sarah_jenkins")
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create candidate
        create_resp = await ac.post(
            "/api/candidates",
            headers=headers,
            json={
                "full_name": "Blank Scanner",
                "email": "scanner@testdomain.com",
            },
        )
        assert create_resp.status_code == 201
        candidate_id = create_resp.json()["id"]

        # 2. Generate blank scanned PDF bytes
        writer = PdfWriter()
        writer.add_blank_page(width=300, height=300)
        pdf_buffer = io.BytesIO()
        writer.write(pdf_buffer)
        pdf_bytes = pdf_buffer.getvalue()

        # 3. Upload PDF
        upload_resp = await ac.post(
            f"/api/candidates/{candidate_id}/resume",
            headers=headers,
            files={"file": ("scanned.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )
        assert upload_resp.status_code == 200

        # 4. Trigger parsing -> must raise 422 with strict message
        parse_resp = await ac.post(
            f"/api/candidates/{candidate_id}/parse-resume",
            headers=headers,
        )
        assert parse_resp.status_code == 422
        assert parse_resp.json()["detail"] == "Unreadable PDF: Please provide a text-based PDF or DOCX format."

        # 5. Verify database recorded parsing_status='failed'
        detail_resp = await ac.get(f"/api/candidates/{candidate_id}", headers=headers)
        resume_record = detail_resp.json()["resumes"][0]
        assert resume_record["parsing_status"] == "failed"
        assert "Unreadable PDF" in resume_record["parsing_error"]


@pytest.mark.asyncio
async def test_job_description_criteria_extraction_endpoint():
    """Test extracting structured criteria from a job description."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        token = await get_auth_token(ac, "sarah_jenkins")
        headers = {"Authorization": f"Bearer {token}"}

        # Create job with structured description
        job_resp = await ac.post(
            "/api/jobs",
            headers=headers,
            json={
                "title": "Principal Distributed Systems Architect",
                "department": "Engineering",
                "raw_description": (
                    "Role Overview:\n"
                    "We need an Architect to guide our platform architecture.\n\n"
                    "Must Have Qualifications:\n"
                    "- 10+ years designing distributed systems in Go and Python.\n"
                    "- Deep understanding of Kafka, PostgreSQL, and Kubernetes.\n\n"
                    "Nice to Have:\n"
                    "- Experience with AWS and GraphQL.\n\n"
                    "Responsibilities:\n"
                    "- Direct system architecture and lead technical reviews.\n"
                    "- Drive high-availability engineering across core services."
                ),
            },
        )
        assert job_resp.status_code == 201
        job_id = job_resp.json()["id"]

        # Trigger JD extraction
        parse_resp = await ac.post(f"/api/jobs/{job_id}/parse-jd", headers=headers)
        assert parse_resp.status_code == 200
        data = parse_resp.json()
        assert data["must_have_count"] > 0
        assert data["responsibilities_count"] > 0
        assert "Python" in data["parsed_criteria"]["required_skills"]

        # Check job details reflect requirements
        detail_resp = await ac.get(f"/api/jobs/{job_id}", headers=headers)
        reqs = detail_resp.json()["requirements"]
        assert len(reqs) > 0


@pytest.mark.asyncio
async def test_cross_tenant_isolation_phase3():
    """Verify other organizations cannot parse or view another organization's candidate resumes or evidence."""
    from tests.test_candidates import create_secondary_org_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        sarah_token = await get_auth_token(ac, "sarah_jenkins")
        _, _, other_org_token = await create_secondary_org_user()
        acme_headers = {"Authorization": f"Bearer {sarah_token}"}
        other_org_headers = {"Authorization": f"Bearer {other_org_token}"}

        # Sarah (Acme) creates candidate
        cand_resp = await ac.post(
            "/api/candidates",
            headers=acme_headers,
            json={"full_name": "Acme Secret Candidate", "email": "secret@acme.com"},
        )
        cand_id = cand_resp.json()["id"]

        # Recruiter from other organization attempts to parse Acme candidate
        cross_parse = await ac.post(f"/api/candidates/{cand_id}/parse-resume", headers=other_org_headers)
        assert cross_parse.status_code == 404

        # Recruiter from other organization attempts to view Acme candidate evidence
        cross_evidence = await ac.get(f"/api/candidates/{cand_id}/evidence", headers=other_org_headers)
        assert cross_evidence.status_code == 404


@pytest.mark.asyncio
async def test_human_evidence_override():
    """Test recruiter overriding an evidence claim."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        token = await get_auth_token(ac, "sarah_jenkins")
        headers = {"Authorization": f"Bearer {token}"}

        # Create candidate & upload resume
        cand_resp = await ac.post(
            "/api/candidates",
            headers=headers,
            json={"full_name": "Audit Candidate", "email": "audit@testdomain.com"},
        )
        candidate_id = cand_resp.json()["id"]

        await ac.post(
            f"/api/candidates/{candidate_id}/resume",
            headers=headers,
            files={"file": ("audit_resume.txt", io.BytesIO(b"Skilled in Python and Docker"), "text/plain")},
        )
        await ac.post(f"/api/candidates/{candidate_id}/parse-resume", headers=headers)

        # Get evidence
        ev_resp = await ac.get(f"/api/candidates/{candidate_id}/evidence", headers=headers)
        evidence_list = ev_resp.json()
        assert len(evidence_list) > 0
        ev_id = evidence_list[0]["id"]

        # Override evidence
        override_resp = await ac.patch(
            f"/api/candidates/{candidate_id}/evidence/{ev_id}/override",
            headers=headers,
            json={"is_overridden_by_human": True, "override_reason": "Verified in technical pre-screening."},
        )
        assert override_resp.status_code == 200
        data = override_resp.json()
        assert data["is_overridden_by_human"] is True
        assert data["override_reason"] == "Verified in technical pre-screening."
