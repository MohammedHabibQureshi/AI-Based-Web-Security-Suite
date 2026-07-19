from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
import json
import logging
from pydantic import BaseModel
from typing import Optional, Dict
from app.db.database import get_db
from app.models.site import Site
from app.models.log import WafLog
from app.rules.rule_engine import rule_engine
from app.ai.ai_provider import ai_provider, redact_text

router = APIRouter()
logger = logging.getLogger("WafCheckAPI")

class WafCheckRequest(BaseModel):
    domain: str
    method: str
    path: str
    headers: Dict[str, str]
    query_params: Optional[str] = ""
    body: Optional[str] = ""
    ip_address: Optional[str] = "127.0.0.1"

class WafCheckResponse(BaseModel):
    blocked: bool
    risk_score: int
    reason: Optional[str] = ""

@router.post("/check", response_model=WafCheckResponse)
def check_request(
    payload: WafCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint for SDK middleware integration. Checks request metadata, evaluates rules/AI,
    logs results, and returns check decisions (blocked true/false).
    """
    # 1. Lookup site domain
    site = db.query(Site).filter(Site.domain == payload.domain).first()
    if not site:
        raise HTTPException(status_code=404, detail=f"Domain {payload.domain} not registered in Web Security Suite WAF.")

    # 2. Run signature inspection
    inspection = rule_engine.inspect_request(
        method=payload.method,
        path=payload.path,
        headers=payload.headers,
        query=payload.query_params,
        body=payload.body
    )

    matched_rules_list = [r["name"] for r in inspection["rules"]]
    risk_score = inspection["risk_score"]
    ai_reason = "Signature matched. Rules evaluated."
    is_blocked = False

    # 3. Borderline check with AI
    if risk_score >= 30 and risk_score < 80:
        ai_result = ai_provider.analyze_waf_request(
            method=payload.method,
            path=payload.path,
            headers=json.dumps(payload.headers),
            query=payload.query_params,
            body=payload.body[:2000],
            matched_rules=matched_rules_list
        )
        if ai_result["is_attack"]:
            risk_score = max(risk_score, ai_result["confidence"])
            ai_reason = ai_result["reasoning"]
        else:
            risk_score = int(risk_score * 0.3)
            ai_reason = f"AI classified request as benign: {ai_result['reasoning']}"
    elif risk_score >= 80:
        ai_reason = "High confidence rule match. Auto-blocked."

    if risk_score >= site.block_threshold:
        is_blocked = True

    # 4. Save WafLog
    try:
        masked_body = redact_text(payload.body[:1000])
        masked_headers = redact_text(json.dumps(payload.headers))

        log_entry = WafLog(
            tenant_id=site.tenant_id,
            site_id=site.id,
            ip_address=payload.ip_address,
            method=payload.method,
            path=payload.path,
            headers=masked_headers,
            query_params=payload.query_params,
            body=masked_body,
            matched_rules=json.dumps(matched_rules_list),
            risk_score=risk_score,
            blocked=is_blocked if site.mode == "Block" else False,
            ai_reasoning=ai_reason
        )
        db.add(log_entry)
        db.commit()
        
        # Trigger real-time WebSocket update
        from app.api.dashboard import manager
        import asyncio
        
        broadcast_payload = {
            "id": log_entry.id,
            "tenant_id": log_entry.tenant_id,
            "site_name": site.name,
            "ip_address": log_entry.ip_address,
            "method": log_entry.method,
            "path": log_entry.path,
            "risk_score": log_entry.risk_score,
            "blocked": log_entry.blocked,
            "matched_rules": matched_rules_list,
            "timestamp": log_entry.timestamp.isoformat()
        }
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(manager.broadcast(broadcast_payload))
            else:
                loop.run_until_complete(manager.broadcast(broadcast_payload))
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Failed to record SDK WafLog: {e}")

    # If Site mode is Log-only (Monitor), we do not ask the SDK to block
    final_block = is_blocked if site.mode == "Block" else False

    return WafCheckResponse(
        blocked=final_block,
        risk_score=risk_score,
        reason=ai_reason
    )
