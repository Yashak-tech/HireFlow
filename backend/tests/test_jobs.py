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
        org_b = Organization(name=f"Beta Corp {uid}", slug=f"beta-corp-{uid}")
        session.add(org_b)
        await session.flush()

        user_b = User(
            org_id=org_b.id,
            email=f"recruiter.{uid}@betacorp.demo",
            full_name="Bob Recruiter",
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
async def test_recruiter_can_create_job():
    """Test 1: Authenticated recruiter can create a job with requirements."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login as Sarah Jenkins (Recruiter)
        login_res = await client.post("/api/auth/demo-login", json={"persona": "sarah_jenkins"})
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create job
        job_payload = {
            "title": "Senior Backend Engineer",
            "department": "Engineering",
            "raw_description": "We are seeking a Senior Backend Engineer proficient in Python and PostgreSQL.",
            "status": "active",
            "requirements": [
                {
                    "requirement_text": "5+ years Python and async frameworks",
                    "requirement_type": "must_have",
                    "category": "skill",
                    "weight": 1.5,
                },
                {
                    "requirement_text": "Production experience with PostgreSQL",
                    "requirement_type": "must_have",
                    "category": "skill",
                    "weight": 1.2,
                },
            ],
        }
        res = await client.post("/api/jobs", json=job_payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "Senior Backend Engineer"
        assert data["department"] == "Engineering"
        assert data["status"] == "active"
        assert len(data["requirements"]) == 2
        assert data["requirements"][0]["requirement_text"] == "5+ years Python and async frameworks"
        assert data["candidate_count"] == 0


@pytest.mark.asyncio
async def test_unauthenticated_user_cannot_create_job():
    """Test 2: Unauthenticated user cannot create a job (HTTP 401)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        job_payload = {
            "title": "Unauthorized Job",
            "department": "Marketing",
            "raw_description": "This job creation should fail without auth credentials.",
        }
        res = await client.post("/api/jobs", json=job_payload)
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_recruiter_can_list_organization_jobs():
    """Test 3: Recruiter can list their organization's jobs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_res = await client.post("/api/auth/demo-login", json={"persona": "sarah_jenkins"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create job
        await client.post(
            "/api/jobs",
            json={
                "title": "Platform Infrastructure Lead",
                "department": "Engineering",
                "raw_description": "Architect core infrastructure and Kubernetes deployments.",
                "status": "active",
            },
            headers=headers,
        )

        res = await client.get("/api/jobs", headers=headers)
        assert res.status_code == 200
        jobs = res.json()
        assert isinstance(jobs, list)
        assert len(jobs) >= 1
        assert any(j["title"] == "Platform Infrastructure Lead" for j in jobs)


@pytest.mark.asyncio
async def test_tenant_isolation_cross_organization_job_access():
    """Test 4: User from Organization B cannot retrieve or update Organization A's job."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Org A (Sarah) creates a job
        login_a = await client.post("/api/auth/demo-login", json={"persona": "sarah_jenkins"})
        token_a = login_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        job_res = await client.post(
            "/api/jobs",
            json={
                "title": "Secret Org A Job",
                "department": "R&D",
                "raw_description": "Confidential proprietary engineering role in Org A.",
            },
            headers=headers_a,
        )
        assert job_res.status_code == 201
        job_id = job_res.json()["id"]

        # Org B (Bob) tries to access Org A's job
        _, _, token_b = await create_secondary_org_user()
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # GET should return 404 (strictly scoped)
        get_res = await client.get(f"/api/jobs/{job_id}", headers=headers_b)
        assert get_res.status_code == 404

        # UPDATE should return 404
        put_res = await client.put(
            f"/api/jobs/{job_id}",
            json={"title": "Hacked Title"},
            headers=headers_b,
        )
        assert put_res.status_code == 404

        # Org B listing should NOT contain Org A's job
        list_res = await client.get("/api/jobs", headers=headers_b)
        assert list_res.status_code == 200
        org_b_jobs = list_res.json()
        assert not any(j["id"] == job_id for j in org_b_jobs)


@pytest.mark.asyncio
async def test_recruiter_can_update_job():
    """Test 5: Recruiter can update job fields and status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_res = await client.post("/api/auth/demo-login", json={"persona": "sarah_jenkins"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create job
        job_res = await client.post(
            "/api/jobs",
            json={
                "title": "Frontend Developer",
                "department": "Design",
                "raw_description": "Original JD text for frontend developer position.",
                "status": "draft",
            },
            headers=headers,
        )
        job_id = job_res.json()["id"]

        # Update title, department, and status
        update_res = await client.put(
            f"/api/jobs/{job_id}",
            json={
                "title": "Lead Frontend Architect",
                "department": "Product Engineering",
                "status": "active",
            },
            headers=headers,
        )
        assert update_res.status_code == 200
        updated = update_res.json()
        assert updated["title"] == "Lead Frontend Architect"
        assert updated["department"] == "Product Engineering"
        assert updated["status"] == "active"

        # Update status directly via /status endpoint
        status_res = await client.patch(
            f"/api/jobs/{job_id}/status",
            json={"status": "paused"},
            headers=headers,
        )
        assert status_res.status_code == 200
        assert status_res.json()["status"] == "paused"


@pytest.mark.asyncio
async def test_invalid_job_payload_validation():
    """Test 12a: Invalid job payload returns 422 validation error."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_res = await client.post("/api/auth/demo-login", json={"persona": "sarah_jenkins"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Missing required fields
        res = await client.post("/api/jobs", json={"title": ""}, headers=headers)
        assert res.status_code == 422

        # Too short description
        res_short = await client.post(
            "/api/jobs",
            json={
                "title": "Test",
                "department": "Dept",
                "raw_description": "short",
            },
            headers=headers,
        )
        assert res_short.status_code == 422
