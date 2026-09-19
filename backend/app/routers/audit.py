"""
Audit Log Router (Phase 6).
Provides searchable audit trails and system provenance records for organizations.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogResponse

router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve chronological audit logs and action provenance.
    Enforces strict organization boundary isolation.
    """
    stmt = (
        select(AuditLog)
        .where(AuditLog.org_id == current_user.org_id)
        .order_by(AuditLog.created_at.desc())
        .limit(min(limit, 500))
    )

    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)

    result = await db.execute(stmt)
    records = result.scalars().all()
    return [AuditLogResponse.model_validate(r) for r in records]
