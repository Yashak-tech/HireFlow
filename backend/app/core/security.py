from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from app.core.config import settings

DEMO_PERSONAS: Dict[str, Dict[str, Any]] = {
    "sarah_jenkins": {
        "email": "sarah.jenkins@hireflow.demo",
        "full_name": "Sarah Jenkins",
        "role": "recruiter",
        "title": "Senior Technical Recruiter",
    },
    "marcus_vance": {
        "email": "marcus.vance@hireflow.demo",
        "full_name": "Marcus Vance",
        "role": "hiring_manager",
        "title": "Director of Engineering",
    },
}


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": now,
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a signed JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None
