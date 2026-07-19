from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class WafLogBase(BaseModel):
    site_id: str
    ip_address: str
    method: str
    path: str
    risk_score: int
    blocked: bool
    timestamp: datetime

class WafLog(WafLogBase):
    id: str
    tenant_id: str
    headers: Optional[str] = None
    query_params: Optional[str] = None
    body: Optional[str] = None
    matched_rules: Optional[str] = None
    ai_reasoning: Optional[str] = None
    site_name: Optional[str] = None # Added for display

    class Config:
        from_attributes = True
class WafLogSummary(WafLogBase):
    id: str
    site_name: Optional[str] = None
    matched_rules: Optional[str] = None

    class Config:
        from_attributes = True
