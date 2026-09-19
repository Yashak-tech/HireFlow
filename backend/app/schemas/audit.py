from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    id: str
    org_id: str
    user_id: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    details: Dict[str, Any] = {}
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
