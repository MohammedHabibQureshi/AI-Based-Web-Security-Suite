from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SiteBase(BaseModel):
    name: str
    domain: str
    origin_url: str
    mode: str = "Block" # Block, Monitor
    block_threshold: int = 50

class SiteCreate(SiteBase):
    pass

class SiteUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    origin_url: Optional[str] = None
    mode: Optional[str] = None
    block_threshold: Optional[int] = None

class Site(SiteBase):
    id: str
    tenant_id: str
    created_at: datetime

    class Config:
        from_attributes = True
