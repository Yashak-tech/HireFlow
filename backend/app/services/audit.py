"""
Audit logging service for tracking system actions, provenance, and recruiter interactions.
"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


async def log_audit_event(
    db: AsyncSession,
    org_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """
    Persist an audit log entry for system traceability.
    Non-blocking / resilient: errors during audit logging are logged without crashing primary flows.
    """
    try:
        entry = AuditLog(
            org_id=org_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry
    except Exception as exc:
        logger.error("Failed to persist audit log event [%s:%s]: %s", action, entity_id, exc)
        return None
