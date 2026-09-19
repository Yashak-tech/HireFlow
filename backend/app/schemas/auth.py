from datetime import datetime
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class DemoLoginRequest(BaseModel):
    persona: Literal["sarah_jenkins", "marcus_vance"] = Field(
        ...,
        description="Demo persona key: sarah_jenkins (Recruiter) or marcus_vance (Hiring Manager)",
    )


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: str
    org_id: str
    email: str
    full_name: str
    role: str
    avatar_url: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    organization: OrganizationResponse
