import os
import uuid
import shutil
import zipfile
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.db.database import get_db, SessionLocal
from app.models.auth import User
from app.models.scan import Scan, ScanFinding
from app.schemas import scan as schemas
from app.api.deps import get_current_user, RoleChecker
from app.scanner.static_scanner import CodeScanner

router = APIRouter()

is_developer = RoleChecker(["Admin", "Developer"])

@router.get("/", response_model=List[schemas.Scan])
def get_scans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Scan).filter(Scan.tenant_id == current_user.tenant_id).order_by(desc(Scan.created_at)).all()

@router.get("/{scan_id}", response_model=schemas.ScanDetail)
def get_scan_detail(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    scan = db.query(Scan).filter(
        Scan.id == scan_id,
        Scan.tenant_id == current_user.tenant_id
    ).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")
    
    findings = db.query(ScanFinding).filter(ScanFinding.scan_id == scan_id).all()
    
    # Structure details
    scan_detail = schemas.ScanDetail.from_orm(scan)
    scan_detail.findings = findings
    return scan_detail


def run_scan_process(tenant_id: str, scan_id: str, zip_path: str, db: Session):
    """
    Synchronous scanning helper that runs SAST scan, then removes zip & extracted dir.
    Can be run in BackgroundTasks or Celery.
    """
    extract_dir = os.path.join(os.path.dirname(zip_path), f"extracted_{scan_id}")
    os.makedirs(extract_dir, exist_ok=True)
    
    try:
        # Extract ZIP
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Run Scan
        scanner = CodeScanner(db, tenant_id)
        scanner.scan_directory(scan_id, extract_dir)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error in scan process {scan_id}: {e}")
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if scan:
            scan.status = "Failed"
            db.commit()
    finally:
        # Cleanup
        if os.path.exists(zip_path):
            os.remove(zip_path)
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir, ignore_errors=True)


@router.post("/upload", response_model=schemas.Scan)
def upload_and_scan(
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(is_developer)
):
    # Ensure it's a ZIP file
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip archives are supported.")

    # Create scan record
    scan = Scan(
        tenant_id=current_user.tenant_id,
        name=name,
        status="Pending",
        score="A",
        total_findings=0
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # Save uploaded file
    upload_dir = os.path.join(os.getcwd(), "tmp_uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    zip_path = os.path.join(upload_dir, f"{scan.id}.zip")
    with open(zip_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Check if Celery can be used (if configured in environment)
    # For robust execution in both modes (with or without Celery background workers running),
    # we fall back to FastAPI BackgroundTasks if Redis is unreachable or Celery is absent.
    use_celery = False
    try:
        from app.core.celery_app import celery_app
        # Check if broker is reachable
        with celery_app.connection() as conn:
            conn.connect()
        use_celery = True
    except Exception:
        pass

    if use_celery:
        from app.worker.tasks import run_background_scan
        run_background_scan.delay(current_user.tenant_id, scan.id, zip_path)
        logger.info(f"Triggered scan {scan.id} via Celery background task.")
    else:
        # Run in FastAPI background tasks with a clean isolated database session
        def bg_scan_wrapper():
            local_db = SessionLocal()
            try:
                run_scan_process(current_user.tenant_id, scan.id, zip_path, local_db)
            finally:
                local_db.close()
        background_tasks.add_task(bg_scan_wrapper)
        logger.info(f"Triggered scan {scan.id} via FastAPI BackgroundTasks (fallback).")

    return scan


@router.post("/clone", response_model=schemas.Scan)
def clone_and_scan(
    background_tasks: BackgroundTasks,
    scan_in: schemas.ScanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_developer)
):
    if not scan_in.repo_url:
        raise HTTPException(status_code=400, detail="repo_url is required for cloning.")

    # Create scan record
    scan = Scan(
        tenant_id=current_user.tenant_id,
        name=scan_in.name,
        repo_url=scan_in.repo_url,
        branch=scan_in.branch or "main",
        status="Pending"
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # Celery vs BackgroundTasks logic
    use_celery = False
    try:
        from app.core.celery_app import celery_app
        with celery_app.connection() as conn:
            conn.connect()
        use_celery = True
    except Exception:
        pass

    if use_celery:
        from app.worker.tasks import run_clone_scan
        run_clone_scan.delay(current_user.tenant_id, scan.id, scan_in.repo_url, scan.branch or "main")
    else:
        # Clone in a background thread using Git stubs or a subprocess
        # We can implement a clean fallback task function in celery tasks.
        from app.worker.tasks import run_clone_scan_process
        def bg_clone_wrapper():
            local_db = SessionLocal()
            try:
                run_clone_scan_process(current_user.tenant_id, scan.id, scan_in.repo_url, scan.branch or "main", local_db)
            finally:
                local_db.close()
        background_tasks.add_task(bg_clone_wrapper)

    return scan
