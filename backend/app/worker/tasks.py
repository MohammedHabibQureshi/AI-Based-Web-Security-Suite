import os
import shutil
import subprocess
import logging
from app.core.celery_app import celery_app
from app.db.database import SessionLocal
from app.scanner.static_scanner import CodeScanner
from app.models.scan import Scan

logger = logging.getLogger("CeleryWorker")

def run_clone_scan_process(tenant_id: str, scan_id: str, repo_url: str, branch: str, db):
    """
    Subprocess git clone runner. Used by both direct threads and celery tasks.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        logger.error(f"Scan {scan_id} not found in DB")
        return

    scan.status = "Running"
    db.commit()

    clone_dir = os.path.join(os.getcwd(), "tmp_uploads", f"clone_{scan_id}")
    os.makedirs(clone_dir, exist_ok=True)

    try:
        # Construct clone url. If public URL, clone directly.
        # Run Git Clone
        logger.info(f"Cloning repository {repo_url} (branch: {branch}) into {clone_dir}")
        cmd = ["git", "clone", "--depth", "1", "-b", branch, repo_url, clone_dir]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        
        if result.returncode != 0:
            # Try cloning default branch (without -b argument)
            logger.info(f"Git clone with branch {branch} failed. Trying to clone the default branch...")
            cmd_default = ["git", "clone", "--depth", "1", repo_url, clone_dir]
            result_default = subprocess.run(cmd_default, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
            
            if result_default.returncode == 0:
                # Succeeded! Let's detect which branch was checked out
                try:
                    detect_branch_cmd = ["git", "-C", clone_dir, "rev-parse", "--abbrev-ref", "HEAD"]
                    detect_res = subprocess.run(detect_branch_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    if detect_res.returncode == 0:
                        detected_branch = detect_res.stdout.strip()
                        logger.info(f"Successfully cloned default branch: {detected_branch}")
                        scan.branch = detected_branch
                        db.commit()
                except Exception as detect_err:
                    logger.warning(f"Could not detect checked out branch name: {detect_err}")
            else:
                # Try a direct HTTP download fallback for github public repos
                if "github.com" in repo_url:
                    logger.info("Git clone failed. Trying ZIP download fallback...")
                    import httpx
                    import zipfile
                    import io
                    
                    # Convert git url to zip url: https://github.com/owner/repo.git -> https://github.com/owner/repo/archive/refs/heads/branch.zip
                    clean_url = repo_url.replace(".git", "")
                    zip_url = f"{clean_url}/archive/refs/heads/{branch}.zip"
                    
                    r = httpx.get(zip_url, follow_redirects=True, timeout=30.0)
                    if r.status_code == 404 and branch == "main":
                        logger.info("Main branch ZIP not found, trying master branch...")
                        zip_url = f"{clean_url}/archive/refs/heads/master.zip"
                        r = httpx.get(zip_url, follow_redirects=True, timeout=30.0)
                        if r.status_code == 200:
                            scan.branch = "master"
                            db.commit()
                            
                    if r.status_code == 200:
                        z = zipfile.ZipFile(io.BytesIO(r.content))
                        z.extractall(clone_dir)
                    else:
                        raise Exception(f"HTTP zip download failed with status code {r.status_code}")
                else:
                    raise Exception(f"Git clone error: {result_default.stderr}")

        # Run Scan
        scanner = CodeScanner(db, tenant_id)
        scanner.scan_directory(scan_id, clone_dir)
        
    except Exception as e:
        logger.error(f"Failed to scan repo {repo_url}: {e}")
        scan.status = "Failed"
        db.commit()
    finally:
        # Cleanup
        if os.path.exists(clone_dir):
            shutil.rmtree(clone_dir, ignore_errors=True)


@celery_app.task(name="app.worker.tasks.run_background_scan")
def run_background_scan(tenant_id: str, scan_id: str, zip_path: str):
    """
    Celery task to run a scan on a ZIP upload.
    """
    logger.info(f"Starting Celery background scan for scan_id: {scan_id}")
    db = SessionLocal()
    try:
        from app.api.scans import run_scan_process
        run_scan_process(tenant_id, scan_id, zip_path, db)
    finally:
        db.close()


@celery_app.task(name="app.worker.tasks.run_clone_scan")
def run_clone_scan(tenant_id: str, scan_id: str, repo_url: str, branch: str):
    """
    Celery task to clone a repository and run a scan.
    """
    logger.info(f"Starting Celery clone-and-scan task for repo: {repo_url}")
    db = SessionLocal()
    try:
        run_clone_scan_process(tenant_id, scan_id, repo_url, branch, db)
    finally:
        db.close()
