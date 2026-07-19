from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ScanFindingBase(BaseModel):
    file_path: str
    line_number: Optional[int] = None
    vulnerability_type: str
    severity: str
    plain_explanation: str
    technical_explanation: str
    suggested_fix_before: Optional[str] = None
    suggested_fix_after: Optional[str] = None

class ScanFinding(ScanFindingBase):
    id: str
    scan_id: str
    tenant_id: str

    class Config:
        from_attributes = True

class ScanBase(BaseModel):
    name: str
    repo_url: Optional[str] = None
    branch: Optional[str] = None

class ScanCreate(ScanBase):
    pass

class Scan(ScanBase):
    id: str
    tenant_id: str
    status: str
    score: str
    total_findings: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ScanDetail(Scan):
    findings: List[ScanFinding] = []
