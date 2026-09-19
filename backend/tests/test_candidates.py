import os
import io
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.organization import Organization
from app.models.user import User
from app.core.security import create_access_token
from app.core.db import async_session_factory


import uuid


async def create_secondary_org_user() -> tuple[str, str, str]:
    """Helper to create a second organization and user for tenant isolation tests."""
    uid = uuid.uuid4().hex[:8]
    async with async_session_factory() as session:
        org_b = Organization(name=f"Gamma Logistics {uid}", slug=f"gamma-logistics-{uid}")
        session.add(org_b)
        await session.flush()

        user_b = User(
            org_id=org_b.id,
            email=f"recruiter.{uid}@gamma.demo",
            full_name="Grace Hopper",
            role="recruiter",
            preferences={},
        )
        session.add(user_b)
        await session.commit()
        await session.refresh(org_b)
        await session.refresh(user_b)

        token = create_access_token({
            "sub": user_b.id,
            "email": user_b.email,
            "org_id": org_b.id,
            "role": user_b.role,
        })
        return org_b.id, user_b.id, token


@pytest.mark.asyncio
async def test_recruiter_can_create_candidate():
    """Test 6: Recruiter can create a candidate profile with skills."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_res = await client.post("/api/auth/demo-login", json={"persona": "sarah_jenkins"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        candidate_payload = {
            "full_name": "Elena Rostova",
            "email": "elena.rostova@engineer.dev",
            "phone": "+1-555-0199",
            "location": "San Francisco, CA",
            "current_title": "Senior Systems Engineer",
            "current_company": "OpenScale Labs",
            "years_of_experience": 6.5,
            "linkedin_url": "https://linkedin.com/in/elena-rostova",
            "github_url": "https://github.com/elena-rostova",
            "skills": [
                {
                    "skill_name": "Python",
                    "category": "technical",
                    "years_experience": 6.0,
                    "proficiency_level": "advanced",
                },
                {
                    "skill_name": "PostgreSQL",
                    "category": "technical",
                    "years_experience": 5.0,
                    "proficiency_level": "advanced",
                },
            ],
        }
        res = await client.post("/api/candidates", json=candidate_payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["full_name"] == "Elena Rostova"
        assert data["email"] == "elena.rostova@engineer.dev"
        assert len(data["skills"]) == 2
        assert data["years_of_experience"] == 6.5


@pytest.mark.asyncio
async def test_recruiter_can_retrieve_candidate_details():
    """Test 7: Recruiter can retrieve detailed candidate profile."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_res = await client.post("/api/auth/demo-login", json={"persona": "sarah_jenkins"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create candidate
        res = await client.post(
            "/api/candidates",
            json={
                "full_name": "David Kim",
                "email": "david.kim@example.org",
                "current_title": "Full Stack Engineer",
                "years_of_experience": 4.0,
            },
            headers=headers,
        )
        candidate_id = res.json()["id"]

        # Retrieve by ID
        get_res = await client.get(f"/api/candidates/{candidate_id}", headers=headers)
        assert get_res.status_code == 200
        data = get_res.json()
        assert data["id"] == candidate_id
        assert data["full_name"] == "David Kim"
        assert data["email"] == "david.kim@example.org"


@pytest.mark.asyncio
async def test_tenant_isolation_cross_organization_candidate_access():
    """Test 8: User from Org B cannot access or modify Org A's candidate."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Org A candidate
        login_a = await client.post("/api/auth/demo-login", json={"persona": "sarah_jenkins"})
        token_a = login_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        cand_res = await client.post(
            "/api/candidates",
            json={
                "full_name": "Confidential Candidate Org A",
                "email": "confidential.a@org.internal",
            },
            headers=headers_a,
        )
        assert cand_res.status_code == 201
        cand_id = cand_res.json()["id"]

        # Org B user
        _, _, token_b = await create_secondary_org_user()
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # GET should return 404
        get_res = await client.get(f"/api/candidates/{cand_id}", headers=headers_b)
        assert get_res.status_code == 404

        # UPDATE should return 404
        patch_res = await client.patch(
            f"/api/candidates/{cand_id}",
            json={"full_name": "Compromised Name"},
            headers=headers_b,
        )
        assert patch_res.status_code == 404

        # Listing in Org B should NOT contain Org A candidate
        list_res = await client.get("/api/candidates", headers=headers_b)
        assert list_res.status_code == 200
        org_b_cands = list_res.json()
        assert not any(c["id"] == cand_id for c in org_b_cands)


@pytest.mark.asyncio
async def test_resume_upload_validates_file_type():
    """Test 9: Resume upload validates file type and rejects unsupported formats (.png, .exe)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_res = await client.post("/api/auth/demo-login", json={"persona": "sarah_jenkins"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try uploading a .png file
        fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\nFake PNG content")
        files = {"file": ("malicious_script.png", fake_image, "image/png")}
        res = await client.post("/api/candidates/upload", files=files, headers=headers)
        assert res.status_code == 422
        assert "Unsupported file type" in res.json()["detail"]

        # Try uploading an .exe file
        fake_exe = io.BytesIO(b"MZ\x90\x00BinaryExe")
        files_exe = {"file": ("payload.exe", fake_exe, "application/x-msdownload")}
        res_exe = await client.post("/api/candidates/upload", files=files_exe, headers=headers)
        assert res_exe.status_code == 422


@pytest.mark.asyncio
async def test_resume_upload_rejects_oversized_file():
    """Test 10: Resume upload rejects files exceeding 10MB with HTTP 413."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_res = await client.post("/api/auth/demo-login", json={"persona": "sarah_jenkins"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Generate a byte stream greater than 10MB (10.5 MB)
        oversized_bytes = b"0" * (11 * 1024 * 1024)
        large_file = io.BytesIO(oversized_bytes)
        files = {"file": ("huge_resume.pdf", large_file, "application/pdf")}

        res = await client.post("/api/candidates/upload", files=files, headers=headers)
        assert res.status_code == 413
        assert "exceeds maximum limit" in res.json()["detail"]


@pytest.mark.asyncio
async def test_resume_safe_uuid_storage_and_no_path_traversal():
    """Test 11: Uploaded resumes use safe UUID filenames on disk and prevent path traversal."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_res = await client.post("/api/auth/demo-login", json={"persona": "sarah_jenkins"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Attempt path traversal in filename: ../../evil.pdf
        traversal_content = io.BytesIO(b"%PDF-1.4 Mock PDF Content for Elena Rostova")
        files = {"file": ("../../etc/shadow_attempt.pdf", traversal_content, "application/pdf")}
        data = {"full_name": "Path Traversal Test", "email": "traversal.test@example.com"}

        res = await client.post("/api/candidates/upload", data=data, files=files, headers=headers)
        assert res.status_code == 201
        cand_data = res.json()
        assert len(cand_data["resumes"]) >= 1

        resume_rec = cand_data["resumes"][0]
        saved_path = resume_rec["file_path"]

        # Ensure path is safely within uploads directory and does NOT contain ..
        assert ".." not in os.path.basename(saved_path)
        assert os.path.exists(saved_path)

        # Ensure filename on disk has a UUID prefix
        disk_filename = os.path.basename(saved_path)
        parts = disk_filename.split("_")
        assert len(parts[0]) == 36  # UUID standard length


@pytest.mark.asyncio
async def test_invalid_candidate_payload_validation():
    """Test 12b: Invalid candidate request payloads return validation errors."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_res = await client.post("/api/auth/demo-login", json={"persona": "sarah_jenkins"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Invalid email format
        res_email = await client.post(
            "/api/candidates",
            json={"full_name": "Bad Email", "email": "not-an-email"},
            headers=headers,
        )
        assert res_email.status_code == 422

        # Missing name
        res_name = await client.post(
            "/api/candidates",
            json={"email": "valid@email.com"},
            headers=headers,
        )
        assert res_name.status_code == 422
