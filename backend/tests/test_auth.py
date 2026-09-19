import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.db import init_db



@pytest.mark.asyncio
async def test_demo_login_sarah_jenkins():
    """Test demo login as Sarah Jenkins (Senior Recruiter)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/demo-login",
            json={"persona": "sarah_jenkins"},
        )
        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["full_name"] == "Sarah Jenkins"
        assert data["user"]["role"] == "recruiter"
        assert data["user"]["email"] == "sarah.jenkins@hireflow.demo"
        assert data["organization"]["slug"] == "acme-tech"
        assert data["organization"]["name"] == "Acme Technologies"


@pytest.mark.asyncio
async def test_demo_login_marcus_vance():
    """Test demo login as Marcus Vance (Hiring Manager)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/demo-login",
            json={"persona": "marcus_vance"},
        )
        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["user"]["full_name"] == "Marcus Vance"
        assert data["user"]["role"] == "hiring_manager"
        assert data["user"]["email"] == "marcus.vance@hireflow.demo"


@pytest.mark.asyncio
async def test_demo_login_invalid_persona():
    """Test that submitting an invalid persona fails validation with HTTP 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/demo-login",
            json={"persona": "invalid_user"},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_current_user_me_authenticated():
    """Test GET /api/auth/me returns current user profile when valid token provided."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Login
        login_resp = await client.post(
            "/api/auth/demo-login",
            json={"persona": "sarah_jenkins"},
        )
        token = login_resp.json()["access_token"]

        # Step 2: Access protected route
        me_resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["user"]["email"] == "sarah.jenkins@hireflow.demo"
        assert me_data["organization"]["slug"] == "acme-tech"


@pytest.mark.asyncio
async def test_protected_routes_unauthenticated():
    """Test that accessing protected routes without token returns HTTP 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 401
        assert "not provided" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_protected_routes_invalid_token():
    """Test that accessing protected routes with forged/invalid token returns HTTP 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer forged-invalid-token-12345"},
        )
        assert resp.status_code == 401
        assert "invalid or expired" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_role_based_access_control():
    """Test role-based access: recruiter allowed, hiring manager forbidden."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login as Sarah (recruiter)
        sarah_login = await client.post("/api/auth/demo-login", json={"persona": "sarah_jenkins"})
        sarah_token = sarah_login.json()["access_token"]

        # 2. Login as Marcus (hiring_manager)
        marcus_login = await client.post("/api/auth/demo-login", json={"persona": "marcus_vance"})
        marcus_token = marcus_login.json()["access_token"]

        # 3. Test recruiter endpoint as Sarah -> 200 OK
        resp_sarah = await client.get(
            "/api/auth/protected-recruiter-only",
            headers={"Authorization": f"Bearer {sarah_token}"},
        )
        assert resp_sarah.status_code == 200
        assert resp_sarah.json()["role"] == "recruiter"

        # 4. Test recruiter endpoint as Marcus -> 403 Forbidden
        resp_marcus = await client.get(
            "/api/auth/protected-recruiter-only",
            headers={"Authorization": f"Bearer {marcus_token}"},
        )
        assert resp_marcus.status_code == 403
        assert "forbidden" in resp_marcus.json()["detail"].lower()
