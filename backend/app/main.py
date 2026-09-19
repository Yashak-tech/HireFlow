from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.db import init_db
from app.routers.auth import router as auth_router
from app.routers.jobs import router as jobs_router
from app.routers.candidates import router as candidates_router
from app.routers.matching import router as matching_router
from app.routers.interviews import router as interviews_router
from app.routers.audit import router as audit_router
from app.routers.stats import router as stats_router
from app.routers.demo import router as demo_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown initialization."""
    # Initialize DB tables and seed demo data on startup
    await init_db()
    yield


app = FastAPI(
    title="HireFlow API",
    description="Intelligent, Auditable AI Recruitment Copilot Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(candidates_router)
app.include_router(matching_router)
app.include_router(interviews_router)
app.include_router(audit_router)
app.include_router(stats_router)
app.include_router(demo_router)


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Phase 0 health check endpoint verifying backend operational readiness."""
    return {
        "status": "healthy",
        "service": "hireflow-api",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "HireFlow API",
        "status": "online",
        "docs": "/docs",
    }
