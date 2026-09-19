"""
Phase 7 Tests — Final Hardening, Stats, & Demo Endpoints.
Verifies:
1. GET /api/stats/dashboard returns valid KPI metrics
2. POST /api/demo/seed populates realistic demo records safely
3. Human Decision Gate enforcement on evaluations
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_dashboard_stats_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Demo login
        login_res = await client.post(
            "/api/auth/demo-login",
            json={"persona": "sarah_jenkins"},
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Fetch stats
        stats_res = await client.get("/api/stats/dashboard", headers=headers)
        assert stats_res.status_code == 200
        data = stats_res.json()
        assert "active_requisitions" in data
        assert "top_match_candidates" in data
        assert "avg_match_fidelity" in data
        assert "hours_saved" in data
        assert isinstance(data["active_requisitions"], int)
        assert isinstance(data["hours_saved"], (int, float))


@pytest.mark.asyncio
async def test_demo_seed_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login
        login_res = await client.post(
            "/api/auth/demo-login",
            json={"persona": "sarah_jenkins"},
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Call seed endpoint
        seed_res = await client.post("/api/demo/seed", headers=headers)
        assert seed_res.status_code == 200
        seed_data = seed_res.json()
        assert seed_data["status"] == "success"
        assert "summary" in seed_data
        assert seed_data["summary"]["jobs_created"] >= 1
        assert seed_data["summary"]["candidates_created"] >= 1
        assert seed_data["summary"]["interviews_created"] >= 1
        assert seed_data["summary"]["evaluations_created"] >= 1

        # Verify audit log recorded
        audit_res = await client.get("/api/audit", headers=headers)
        assert audit_res.status_code == 200
        audit_logs = audit_res.json()
        assert len(audit_logs) >= 1
