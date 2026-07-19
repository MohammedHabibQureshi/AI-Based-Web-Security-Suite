from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.auth import User
from app.models.log import WafLog
from app.models.site import Site
from app.schemas import log as schemas
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[schemas.WafLogSummary])
def get_logs(
    site_id: Optional[str] = None,
    blocked: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(WafLog).filter(WafLog.tenant_id == current_user.tenant_id)
    
    if site_id:
        query = query.filter(WafLog.site_id == site_id)
    if blocked is not None:
        query = query.filter(WafLog.blocked == blocked)
        
    logs = query.order_by(desc(WafLog.timestamp)).offset(offset).limit(limit).all()
    
    # Enrich with site name
    results = []
    for log in logs:
        site = db.query(Site).filter(Site.id == log.site_id).first()
        log_dict = schemas.WafLogSummary.from_orm(log)
        log_dict.site_name = site.name if site else "Unknown Site"
        results.append(log_dict)
        
    return results

@router.get("/{log_id}", response_model=schemas.WafLog)
def get_log_detail(
    log_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    log = db.query(WafLog).filter(
        WafLog.id == log_id,
        WafLog.tenant_id == current_user.tenant_id
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found.")
        
    site = db.query(Site).filter(Site.id == log.site_id).first()
    
    response = schemas.WafLog.from_orm(log)
    response.site_name = site.name if site else "Unknown Site"
    return response
