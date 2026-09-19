import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Verify that the Phase 0 health endpoint returns HTTP 200 and healthy status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "hireflow-api"
        assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_root_endpoint():
    """Verify that root endpoint responds successfully."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "online"


@pytest.mark.asyncio
async def test_cors_preflight_vercel_origin():
    """Verify that CORS preflight request from the Vercel frontend is accepted."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {
            "Origin": "https://hire-flow-nu-blush.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        }
        response = await client.options("/api/auth/demo-login", headers=headers)
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "https://hire-flow-nu-blush.vercel.app"
        assert response.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.asyncio
async def test_cors_disallowed_origin():
    """Verify that an untrusted origin is rejected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {
            "Origin": "https://unauthorized-malicious-site.com",
            "Access-Control-Request-Method": "POST",
        }
        response = await client.options("/api/auth/demo-login", headers=headers)
        assert response.status_code == 400

