import os
import json
import logging
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta
from sqlalchemy import func
from app.db.database import SessionLocal
from app.models.scan import Scan, ScanFinding
from app.models.log import WafLog
from app.models.site import Site

logger = logging.getLogger(__name__)

# Try to import WeasyPrint
try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except Exception as e:
    logger.warning(f"WeasyPrint could not be imported (missing system library/Gtk?): {e}.")
    WEASYPRINT_AVAILABLE = False

# Try to import xhtml2pdf as a fallback
try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except Exception as e:
    logger.warning(f"xhtml2pdf could not be imported: {e}")
    XHTML2PDF_AVAILABLE = False


def generate_svg_pie_chart(critical: int, high: int, medium: int, low: int) -> str:
    """
    Generates a clean inline SVG pie chart for severity distribution.
    """
    total = critical + high + medium + low
    if total == 0:
        return ""

    # Colors
    colors = {
        "critical": "#ef4444", # Red
        "high": "#f97316",     # Orange
        "medium": "#eab308",   # Yellow
        "low": "#3b82f6"       # Blue
    }

    # Percentages
    pct_crit = (critical / total) * 100
    pct_high = (high / total) * 100
    pct_med = (medium / total) * 100
    pct_low = (low / total) * 100

    # Calculate stroke dashes (for a circle of radius 15.915, circumference is 100)
    dash_crit = pct_crit
    dash_high = pct_high
    dash_med = pct_med
    dash_low = pct_low

    offset_crit = 100
    offset_high = 100 - dash_crit
    offset_med = 100 - dash_crit - dash_high
    offset_low = 100 - dash_crit - dash_high - dash_med

    svg = f"""
    <svg width="220" height="220" viewBox="0 0 42 42" class="donut">
      <circle class="donut-hole" cx="21" cy="21" r="15.91549430918954" fill="transparent"></circle>
      <circle class="donut-ring" cx="21" cy="21" r="15.91549430918954" fill="transparent" stroke="#1e293b" stroke-width="5"></circle>

      {f'<circle class="donut-segment" cx="21" cy="21" r="15.91549430918954" fill="transparent" stroke="{colors["critical"]}" stroke-width="5.3" stroke-dasharray="{dash_crit} {100 - dash_crit}" stroke-dashoffset="{offset_crit}"></circle>' if dash_crit > 0 else ''}
      {f'<circle class="donut-segment" cx="21" cy="21" r="15.91549430918954" fill="transparent" stroke="{colors["high"]}" stroke-width="5.3" stroke-dasharray="{dash_high} {100 - dash_high}" stroke-dashoffset="{offset_high}"></circle>' if dash_high > 0 else ''}
      {f'<circle class="donut-segment" cx="21" cy="21" r="15.91549430918954" fill="transparent" stroke="{colors["medium"]}" stroke-width="5.3" stroke-dasharray="{dash_med} {100 - dash_med}" stroke-dashoffset="{offset_med}"></circle>' if dash_med > 0 else ''}
      {f'<circle class="donut-segment" cx="21" cy="21" r="15.91549430918954" fill="transparent" stroke="{colors["low"]}" stroke-width="5.3" stroke-dasharray="{dash_low} {100 - dash_low}" stroke-dashoffset="{offset_low}"></circle>' if dash_low > 0 else ''}

      <g class="chart-text">
        <text x="50%" y="50%" class="chart-number" dy="-2" font-size="6" text-anchor="middle" fill="#f1f5f9" font-weight="bold">{total}</text>
        <text x="50%" y="50%" class="chart-label" dy="4" font-size="2" text-anchor="middle" fill="#94a3b8" letter-spacing="0.1">TOTAL ISSUES</text>
      </g>
    </svg>
    """
    return svg

def generate_svg_waf_trend(waf_logs_7d: list) -> str:
    """
    Generates a line graph showing blocked requests over the last 7 days.
    """
    if not waf_logs_7d:
        return ""

    width = 500
    height = 150
    padding = 25

    max_blocks = max([day["blocks"] for day in waf_logs_7d] + [5]) # Ensure min scale of 5
    
    # Generate points
    points = []
    num_days = len(waf_logs_7d)
    x_step = (width - 2 * padding) / max((num_days - 1), 1)
    
    for idx, day in enumerate(waf_logs_7d):
        x = padding + idx * x_step
        # Invert y since SVG 0 is top
        y = height - padding - (day["blocks"] / max_blocks) * (height - 2 * padding)
        points.append((x, y))

    path_d = f"M {points[0][0]} {points[0][1]} "
    for x, y in points[1:]:
        path_d += f"L {x} {y} "

    # SVG points
    dots = ""
    labels = ""
    for idx, (x, y) in enumerate(points):
        day_label = waf_logs_7d[idx]["date"]
        val = waf_logs_7d[idx]["blocks"]
        dots += f'<circle cx="{x}" cy="{y}" r="4" fill="#ef4444" stroke="#020617" stroke-width="1.5"></circle>'
        dots += f'<text x="{x}" y="{y - 8}" fill="#f1f5f9" font-size="9" text-anchor="middle" font-family="sans-serif">{val}</text>'
        labels += f'<text x="{x}" y="{height - 5}" fill="#64748b" font-size="9" text-anchor="middle" font-family="sans-serif">{day_label}</text>'

    svg = f"""
    <svg width="100%" height="100%" viewBox="0 0 {width} {height}" style="background: #0f172a; border-radius: 8px; border: 1px solid #1e293b;">
      <!-- Grid lines -->
      <line x1="{padding}" y1="{padding}" x2="{width - padding}" y2="{padding}" stroke="#1e293b" stroke-dasharray="2 2" />
      <line x1="{padding}" y1="{height/2}" x2="{width - padding}" y2="{height/2}" stroke="#1e293b" stroke-dasharray="2 2" />
      <line x1="{padding}" y1="{height - padding}" x2="{width - padding}" y2="{height - padding}" stroke="#334155" />

      <!-- Area Path -->
      <path d="{path_d} L {points[-1][0]} {height - padding} L {points[0][0]} {height - padding} Z" fill="url(#grad)" opacity="0.15" />

      <!-- Trend Line -->
      <path d="{path_d}" fill="none" stroke="#ef4444" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />

      <!-- Gradients -->
      <defs>
        <linearGradient id="grad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#ef4444" />
          <stop offset="100%" stop-color="#ef4444" stop-opacity="0" />
        </linearGradient>
      </defs>

      <!-- Dots & Labels -->
      {dots}
      {labels}
    </svg>
    """
    return svg


class ReportGenerator:
    def __init__(self):
        # Setup Jinja environment
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(current_dir, "templates")
        os.makedirs(template_dir, exist_ok=True)
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def build_report_data(self, tenant_id: str, scan_id: Optional[str] = None) -> dict:
        """
        Gathers WAF and Scan findings data for rendering into the report template.
        """
        db = SessionLocal()
        try:
            # 1. Fetch Tenant/Site details
            # Get latest scan if no scan_id is provided
            scan = None
            findings = []
            if scan_id:
                scan = db.query(Scan).filter(Scan.id == scan_id, Scan.tenant_id == tenant_id).first()
            else:
                scan = db.query(Scan).filter(Scan.tenant_id == tenant_id).order_by(Scan.created_at.desc()).first()

            if scan:
                findings = db.query(ScanFinding).filter(ScanFinding.scan_id == scan.id).all()

            # Count severities
            severities = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
            for f in findings:
                severities[f.severity] = severities.get(f.severity, 0) + 1

            # 2. Get WAF metrics
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            total_blocked = db.query(WafLog).filter(
                WafLog.tenant_id == tenant_id,
                WafLog.blocked == True,
                WafLog.timestamp >= thirty_days_ago
            ).count()

            # Group top attack types
            top_attacks_raw = db.query(WafLog.matched_rules, func.count(WafLog.id)).filter(
                WafLog.tenant_id == tenant_id,
                WafLog.blocked == True,
                WafLog.timestamp >= thirty_days_ago
            ).group_by(WafLog.matched_rules).all()

            top_attacks = {}
            for match_str, count in top_attacks_raw:
                if not match_str:
                    continue
                try:
                    names = json.loads(match_str)
                    for n in names:
                        top_attacks[n] = top_attacks.get(n, 0) + count
                except Exception:
                    pass

            sorted_attacks = sorted(top_attacks.items(), key=lambda x: x[1], reverse=True)[:5]

            # Top offending IPs
            top_ips = db.query(WafLog.ip_address, func.count(WafLog.id)).filter(
                WafLog.tenant_id == tenant_id,
                WafLog.blocked == True,
                WafLog.timestamp >= thirty_days_ago
            ).group_by(WafLog.ip_address).order_by(func.count(WafLog.id).desc()).limit(5).all()

            # 7-day WAF block logs for line chart
            trend_data = []
            for i in range(7):
                day = datetime.utcnow() - timedelta(days=i)
                day_start = datetime(day.year, day.month, day.day, 0, 0, 0)
                day_end = datetime(day.year, day.month, day.day, 23, 59, 59)
                blocks_count = db.query(WafLog).filter(
                    WafLog.tenant_id == tenant_id,
                    WafLog.blocked == True,
                    WafLog.timestamp >= day_start,
                    WafLog.timestamp <= day_end
                ).count()
                trend_data.append({
                    "date": day_start.strftime("%b %d"),
                    "blocks": blocks_count
                })
            trend_data.reverse()

            # Generate SVGs
            donut_chart = generate_svg_pie_chart(
                severities["Critical"], severities["High"], severities["Medium"], severities["Low"]
            )
            line_chart = generate_svg_waf_trend(trend_data)

            # Build data object
            report_data = {
                "scan": scan,
                "findings": findings,
                "severities": severities,
                "waf_total_blocked_30d": total_blocked,
                "waf_top_attacks": sorted_attacks,
                "waf_top_ips": top_ips,
                "donut_chart": donut_chart,
                "line_chart": line_chart,
                "waf_trend_data": trend_data,
                "generated_at": datetime.utcnow().strftime("%B %d, %Y %H:%M UTC"),
                "risk_score_grade": scan.score if scan else "A",
                "weasyprint_available": WEASYPRINT_AVAILABLE
            }
            return report_data
        finally:
            db.close()

    def generate_html_report(self, tenant_id: str, scan_id: Optional[str] = None) -> str:
        """
        Renders the Jinga HTML template with security suite data.
        """
        data = self.build_report_data(tenant_id, scan_id)
        # Load or create basic HTML template
        try:
            template = self.env.get_template("report_template.html")
        except Exception:
            # Fallback to local default string if template not found yet
            return "<html><body><h1>Report Template Missing</h1></body></html>"
        
        return template.render(**data)

    def generate_pdf(self, tenant_id: str, scan_id: Optional[str] = None) -> tuple:
        """
        Generates the PDF bytes or returns HTML fallback.
        Returns: (bytes, content_type)
        """
        html_content = self.generate_html_report(tenant_id, scan_id)
        
        if WEASYPRINT_AVAILABLE:
            try:
                pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
                return pdf_bytes, "application/pdf"
            except Exception as e:
                logger.error(f"WeasyPrint rendering failed: {e}. Falling back to xhtml2pdf.")
                
        if XHTML2PDF_AVAILABLE:
            try:
                import io
                import re
                # Clean nested rules inside @page for xhtml2pdf parser compatibility
                cleaned_html = re.sub(r'@bottom-right\s*{[^}]+}', '', html_content)
                
                pdf_buffer = io.BytesIO()
                pisa_status = pisa.CreatePDF(cleaned_html, dest=pdf_buffer)
                if not pisa_status.err:
                    return pdf_buffer.getvalue(), "application/pdf"
                else:
                    logger.error(f"xhtml2pdf rendering status error: {pisa_status.err}")
            except Exception as e:
                logger.error(f"xhtml2pdf rendering failed: {e}")

        # Fallback to HTML
        return html_content.encode("utf-8"), "text/html"

report_generator = ReportGenerator()
