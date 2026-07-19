from fastapi import APIRouter, Depends, HTTPException, Response
from app.db.database import get_db
from app.models.auth import User
from app.api.deps import get_current_user
from app.reports.pdf_generator import report_generator

router = APIRouter()

@router.get("/download/{scan_id}")
def download_pdf_report(
    scan_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        pdf_bytes, mime_type = report_generator.generate_pdf(current_user.tenant_id, scan_id)
        
        filename = f"Web_Security_Suite_Report_{scan_id}.pdf" if mime_type == "application/pdf" else f"Web_Security_Suite_Report_{scan_id}.html"
        
        headers = {
            "Content-Disposition": f"attachment; filename={filename}"
        }
        return Response(content=pdf_bytes, media_type=mime_type, headers=headers)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to generate report for download: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate security report: {e}")

@router.get("/preview/{scan_id}")
def preview_html_report(
    scan_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        html_content = report_generator.generate_html_report(current_user.tenant_id, scan_id)
        return Response(content=html_content, media_type="text/html")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to generate preview report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to render report preview: {e}")
