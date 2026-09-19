from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_db
from app.core.security import create_access_token, DEMO_PERSONAS
from app.core.deps import get_current_user, get_current_org, require_role
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import DemoLoginRequest, TokenResponse, UserResponse, OrganizationResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/demo-login", response_model=TokenResponse)
async def demo_login(
    payload: DemoLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate via quick Demo Persona Switch (Sarah Jenkins or Marcus Vance)."""
    persona_key = payload.persona
    persona_meta = DEMO_PERSONAS.get(persona_key)

    if not persona_meta:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown demo persona '{persona_key}'. Available: {list(DEMO_PERSONAS.keys())}",
        )

    # Find the user by demo email
    result = await db.execute(select(User).where(User.email == persona_meta["email"]))
    user = result.scalar_one_or_none()

    if not user:
        # If demo user not yet created, link to default org or create
        org_result = await db.execute(select(Organization).limit(1))
        org = org_result.scalar_one_or_none()
        if not org:
            org = Organization(name="Acme Technologies", slug="acme-tech")
            db.add(org)
            await db.flush()

        user = User(
            org_id=org.id,
            email=persona_meta["email"],
            full_name=persona_meta["full_name"],
            role=persona_meta["role"],
            preferences={"persona_id": persona_key, "title": persona_meta["title"]},
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Fetch organization
    org_result = await db.execute(select(Organization).where(Organization.id == user.org_id))
    org = org_result.scalar_one()

    # Generate JWT
    access_token = create_access_token(data={
        "sub": user.id,
        "email": user.email,
        "org_id": user.org_id,
        "role": user.role,
    })

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
        organization=OrganizationResponse.model_validate(org),
    )


@router.get("/me")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """Protected endpoint returning the active authenticated user and tenant organization."""
    return {
        "user": UserResponse.model_validate(current_user),
        "organization": OrganizationResponse.model_validate(org),
    }


@router.get("/protected-recruiter-only")
async def protected_recruiter_endpoint(
    current_user: User = Depends(require_role(["recruiter"])),
):
    """Protected test endpoint accessible only to users with the 'recruiter' role."""
    return {
        "message": f"Hello {current_user.full_name}, you have verified recruiter access.",
        "role": current_user.role,
    }
