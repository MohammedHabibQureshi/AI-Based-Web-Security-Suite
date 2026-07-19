from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import json
from typing import List
from app.db.database import get_db
from app.models.auth import User
from app.models.site import Site
from app.models.log import WafLog
from app.models.scan import Scan, ScanFinding
from app.api.deps import get_current_user

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        # Create a list of connections to clean up if send fails
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            self.disconnect(dead)

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive by receiving messages (ping-pong)
            data = await websocket.receive_text()
            # Echo back or keepalive check
            await websocket.send_text(json.dumps({"status": "alive"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.get("/metrics")
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tenant_id = current_user.tenant_id

    # 1. Total Protected Sites
    total_sites = db.query(Site).filter(Site.tenant_id == tenant_id).count()

    # 2. WAF Stats (past 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    total_blocks = db.query(WafLog).filter(
        WafLog.tenant_id == tenant_id,
        WafLog.blocked == True,
        WafLog.timestamp >= thirty_days_ago
    ).count()

    total_requests = db.query(WafLog).filter(
        WafLog.tenant_id == tenant_id,
        WafLog.timestamp >= thirty_days_ago
    ).count()

    unique_attacker_ips = db.query(func.count(func.distinct(WafLog.ip_address))).filter(
        WafLog.tenant_id == tenant_id,
        WafLog.blocked == True,
        WafLog.timestamp >= thirty_days_ago
    ).scalar() or 0

    # 3. Vulnerability scanner stats (accumulated latest scan per repo)
    # We query all scan findings for latest scan of each scan name
    subquery = db.query(
        Scan.name,
        func.max(Scan.created_at).label("max_created")
    ).filter(
        Scan.tenant_id == tenant_id, 
        Scan.status == "Completed"
    ).group_by(Scan.name).subquery()

    latest_scans = db.query(Scan).join(
        subquery,
        (Scan.name == subquery.c.name) & (Scan.created_at == subquery.c.max_created)
    ).all()

    vulnerabilities = {
        "Critical": 0,
        "High": 0,
        "Medium": 0,
        "Low": 0
    }
    for ls in latest_scans:
        findings = db.query(ScanFinding).filter(ScanFinding.scan_id == ls.id).all()
        for f in findings:
            vulnerabilities[f.severity] = vulnerabilities.get(f.severity, 0) + 1

    # 4. History of blocks (past 7 days for trend charts)
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
        
        total_count = db.query(WafLog).filter(
            WafLog.tenant_id == tenant_id,
            WafLog.timestamp >= day_start,
            WafLog.timestamp <= day_end
        ).count()

        trend_data.append({
            "date": day_start.strftime("%b %d"),
            "blocks": blocks_count,
            "requests": total_count
        })

    trend_data.reverse()

    return {
        "total_sites": total_sites,
        "total_blocks_30d": total_blocks,
        "total_requests_30d": total_requests,
        "unique_attackers": unique_attacker_ips,
        "vulnerabilities": vulnerabilities,
        "waf_trend": trend_data
    }
