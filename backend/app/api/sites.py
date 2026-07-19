from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.auth import User
from app.models.site import Site
from app.schemas import site as schemas
from app.api.deps import get_current_user, RoleChecker

router = APIRouter()

# Role checkers
is_developer = RoleChecker(["Admin", "Developer"])
is_admin = RoleChecker(["Admin"])

@router.get("/", response_model=List[schemas.Site])
def get_sites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Multi-tenant filter
    return db.query(Site).filter(Site.tenant_id == current_user.tenant_id).all()

@router.post("/", response_model=schemas.Site, status_code=status.HTTP_201_CREATED)
def create_site(
    site_in: schemas.SiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_developer)
):
    # Prevent duplicate domains
    existing = db.query(Site).filter(Site.domain == site_in.domain).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain name is already registered."
        )

    site = Site(
        tenant_id=current_user.tenant_id,
        name=site_in.name,
        domain=site_in.domain,
        origin_url=site_in.origin_url,
        mode=site_in.mode,
        block_threshold=site_in.block_threshold
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return site

@router.put("/{site_id}", response_model=schemas.Site)
def update_site(
    site_id: str,
    site_in: schemas.SiteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_developer)
):
    site = db.query(Site).filter(
        Site.id == site_id,
        Site.tenant_id == current_user.tenant_id
    ).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found.")

    update_data = site_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(site, field, value)

    db.commit()
    db.refresh(site)
    return site

@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_site(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
):
    site = db.query(Site).filter(
        Site.id == site_id,
        Site.tenant_id == current_user.tenant_id
    ).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found.")
    
    db.delete(site)
    db.commit()
    return None
