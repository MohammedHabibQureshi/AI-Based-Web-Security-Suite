import json
import logging
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from app.core.config import settings
from app.db.database import SessionLocal
from app.models.site import Site
from app.models.log import WafLog
from app.rules.rule_engine import rule_engine
from app.ai.ai_provider import ai_provider

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WAF_Proxy")

app = FastAPI(title="Web Security Suite WAF Proxy")

# Keep a list of active websocket connections to broadcast blocked requests in real time
active_connections = []

def broadcast_waf_log(log_data: dict):
    """
    Sends WAF logs to any listening WebSocket clients.
    """
    import asyncio
    from app.api.dashboard import manager
    
    # Run the manager broadcast as an async task
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    if loop.is_running():
        loop.create_task(manager.broadcast(log_data))
    else:
        loop.run_until_complete(manager.broadcast(log_data))


blocked_page_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Access Denied - Web Security Suite</title>
    <style>
        body {{
            background: radial-gradient(circle at center, #0f172a, #020617);
            color: #f1f5f9;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            overflow: hidden;
        }}
        .card {{
            background: rgba(30, 41, 59, 0.4);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 16px;
            padding: 40px;
            max-width: 500px;
            text-align: center;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            animation: fadeIn 0.6s ease-out;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .shield {{
            background: rgba(239, 68, 68, 0.1);
            border: 2px solid #ef4444;
            border-radius: 50%;
            width: 80px;
            height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 24px;
            color: #ef4444;
            font-size: 40px;
            font-weight: bold;
            box-shadow: 0 0 20px rgba(239, 68, 68, 0.2);
        }}
        h1 {{
            font-size: 28px;
            margin: 0 0 12px;
            font-weight: 700;
            letter-spacing: -0.025em;
        }}
        p {{
            color: #94a3b8;
            font-size: 16px;
            line-height: 1.6;
            margin: 0 0 24px;
        }}
        .details {{
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 16px;
            font-family: monospace;
            font-size: 13px;
            color: #cbd5e1;
            text-align: left;
            margin-bottom: 24px;
            word-break: break-all;
        }}
        .detail-item {{
            margin-bottom: 8px;
        }}
        .detail-item:last-child {{
            margin-bottom: 0;
        }}
        .label {{
            color: #64748b;
            font-weight: bold;
        }}
        .footer {{
            font-size: 12px;
            color: #475569;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="shield">!</div>
        <h1>Request Blocked</h1>
        <p>Your request was flagged as potentially harmful and has been blocked by Web Security Suite Web Application Firewall.</p>
        
        <div class="details">
            <div class="detail-item"><span class="label">Event ID:</span> {event_id}</div>
            <div class="detail-item"><span class="label">IP Address:</span> {ip_address}</div>
            <div class="detail-item"><span class="label">Reason:</span> {reason}</div>
            <div class="detail-item"><span class="label">Risk Score:</span> {risk_score}/100</div>
        </div>

        <div class="footer">
            Protected by Web Security Suite Security Engine
        </div>
    </div>
</body>
</html>
"""
def render_json_visualizer(data, path: str, method: str, origin_url: str) -> str:
    import html
    
    # Format JSON with indentation for the raw view
    raw_json_str = json.dumps(data, indent=2)
    escaped_raw_json = html.escape(raw_json_str)
    
    # Build visual representation
    visual_html = ""
    
    if isinstance(data, list):
        visual_html += '<div class="cards-grid">'
        for idx, item in enumerate(data):
            visual_html += f'<div class="card"><div class="card-header">Item #{idx + 1}</div><div class="card-body">'
            if isinstance(item, dict):
                for k, v in item.items():
                    val_str = html.escape(str(v))
                    visual_html += f'<div class="card-row"><span class="card-key">{html.escape(str(k))}:</span> <span class="card-val">{val_str}</span></div>'
            else:
                visual_html += f'<div class="card-row"><span class="card-val">{html.escape(str(item))}</span></div>'
            visual_html += '</div></div>'
        visual_html += '</div>'
    elif isinstance(data, dict):
        visual_html += '<div class="table-container"><table><thead><tr><th>Field / Key</th><th>Value</th></tr></thead><tbody>'
        for k, v in data.items():
            val_str = html.escape(str(v))
            if isinstance(v, (dict, list)):
                val_str = f'<pre class="nested-json">{html.escape(json.dumps(v, indent=2))}</pre>'
            visual_html += f'<tr><td class="key-cell">{html.escape(str(k))}</td><td class="val-cell">{val_str}</td></tr>'
        visual_html += '</tbody></table></div>'
    else:
        visual_html += f'<div class="primitive-val">{html.escape(str(data))}</div>'

    # Build the final page
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Security Suite Proxy - Visual Inspector</title>
    <style>
        body {{
            background-color: #030712;
            color: #f3f4f6;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            margin: 0;
            padding: 0;
            min-height: 100vh;
        }}
        header {{
            background: linear-gradient(135deg, #1e1b4b 0%, #030712 100%);
            border-bottom: 1px solid #1f2937;
            padding: 20px 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .brand {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .logo-shield {{
            background: linear-gradient(135deg, #4f46e5 0%, #3730a3 100%);
            border-radius: 8px;
            padding: 6px 12px;
            font-weight: 800;
            color: #ffffff;
            font-size: 18px;
            box-shadow: 0 0 15px rgba(79, 70, 229, 0.4);
        }}
        .title-text {{
            font-size: 20px;
            font-weight: 700;
            letter-spacing: -0.025em;
        }}
        .badge-proxy {{
            background-color: #312e81;
            color: #a5b4fc;
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 4px;
            border: 1px solid #4338ca;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .container {{
            max-width: 1200px;
            margin: 40px auto;
            padding: 0 20px;
        }}
        .url-banner {{
            background-color: #111827;
            border: 1px solid #374151;
            border-radius: 12px;
            padding: 16px 24px;
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 30px;
        }}
        .method-badge {{
            background-color: #065f46;
            color: #34d399;
            font-family: monospace;
            font-weight: bold;
            font-size: 14px;
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid #059669;
        }}
        .url-text {{
            font-family: monospace;
            font-size: 15px;
            color: #e5e7eb;
            word-break: break-all;
            flex-grow: 1;
        }}
        .tabs-header {{
            display: flex;
            gap: 8px;
            border-bottom: 1px solid #1f2937;
            margin-bottom: 24px;
        }}
        .tab-btn {{
            background: none;
            border: none;
            color: #9ca3af;
            font-size: 15px;
            font-weight: 600;
            padding: 12px 20px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s ease;
        }}
        .tab-btn:hover {{
            color: #e5e7eb;
        }}
        .tab-btn.active {{
            color: #6366f1;
            border-bottom-color: #6366f1;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        /* Visualizer Tables */
        .table-container {{
            background-color: #111827;
            border: 1px solid #1f2937;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        th, td {{
            padding: 16px 24px;
            border-bottom: 1px solid #1f2937;
        }}
        th {{
            background-color: #1f2937;
            color: #9ca3af;
            font-weight: 600;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .key-cell {{
            font-weight: 600;
            color: #818cf8;
            width: 250px;
            word-break: break-all;
        }}
        .val-cell {{
            color: #e5e7eb;
            word-break: break-all;
            line-height: 1.6;
        }}
        tr:last-child th, tr:last-child td {{
            border-bottom: none;
        }}
        /* Visualizer Cards (Lists) */
        .cards-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 24px;
        }}
        .card {{
            background-color: #111827;
            border: 1px solid #1f2937;
            border-radius: 12px;
            overflow: hidden;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}
        .card:hover {{
            transform: translateY(-2px);
            border-color: #374151;
        }}
        .card-header {{
            background-color: #1f2937;
            padding: 12px 20px;
            font-weight: 700;
            font-size: 14px;
            color: #cbd5e1;
            border-bottom: 1px solid #374151;
        }}
        .card-body {{
            padding: 20px;
        }}
        .card-row {{
            margin-bottom: 12px;
            line-height: 1.5;
        }}
        .card-row:last-child {{
            margin-bottom: 0;
        }}
        .card-key {{
            font-weight: 600;
            color: #818cf8;
            margin-right: 6px;
        }}
        .card-val {{
            color: #cbd5e1;
            word-break: break-all;
        }}
        /* Primitive val styling */
        .primitive-val {{
            background-color: #111827;
            border: 1px solid #1f2937;
            border-radius: 12px;
            padding: 24px;
            font-size: 18px;
            font-family: monospace;
            text-align: center;
        }}
        /* Nested JSON structure */
        .nested-json {{
            background-color: #030712;
            border: 1px solid #1f2937;
            border-radius: 6px;
            padding: 12px;
            font-family: monospace;
            font-size: 13px;
            color: #e5e7eb;
            overflow-x: auto;
            margin: 4px 0 0 0;
        }}
        /* Raw JSON block */
        .raw-container {{
            position: relative;
            background-color: #111827;
            border: 1px solid #1f2937;
            border-radius: 12px;
            padding: 24px;
            overflow: hidden;
        }}
        .copy-btn {{
            position: absolute;
            top: 16px;
            right: 16px;
            background-color: #1f2937;
            color: #cbd5e1;
            border: 1px solid #374151;
            padding: 6px 14px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s ease;
        }}
        .copy-btn:hover {{
            background-color: #374151;
            color: #ffffff;
        }}
        pre.raw-code {{
            margin: 0;
            font-family: monospace;
            font-size: 14px;
            color: #a7f3d0;
            overflow-x: auto;
            line-height: 1.5;
            max-height: 60vh;
        }}
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <div class="logo-shield">W</div>
            <span class="title-text">Web Security Suite Proxy</span>
            <span class="badge-proxy">Visual Inspector</span>
        </div>
        <div style="font-size: 13px; color: #64748b;">
            Secure Gateway Active
        </div>
    </header>

    <div class="container">
        <div class="url-banner">
            <span class="method-badge">{method}</span>
            <span class="url-text">{html.escape(origin_url.rstrip('/'))}{html.escape(path)}</span>
        </div>

        <div class="tabs-header">
            <button class="tab-btn active" onclick="switchTab('visual')">Visual Inspector</button>
            <button class="tab-btn" onclick="switchTab('raw')">Raw JSON</button>
        </div>

        <!-- Visual Tab Content -->
        <div id="visual-tab" class="tab-content active">
            {visual_html}
        </div>

        <!-- Raw JSON Tab Content -->
        <div id="raw-tab" class="tab-content">
            <div class="raw-container">
                <button class="copy-btn" onclick="copyRawJson()">Copy JSON</button>
                <pre class="raw-code"><code id="raw-json-text">{escaped_raw_json}</code></pre>
            </div>
        </div>
    </div>

    <script>
        function switchTab(tabId) {{
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            if (tabId === 'visual') {{
                document.querySelectorAll('.tab-btn')[0].classList.add('active');
                document.getElementById('visual-tab').classList.add('active');
            }} else {{
                document.querySelectorAll('.tab-btn')[1].classList.add('active');
                document.getElementById('raw-tab').classList.add('active');
            }}
        }}

        function copyRawJson() {{
            const text = document.getElementById('raw-json-text').innerText;
            navigator.clipboard.writeText(text).then(() => {{
                const btn = document.querySelector('.copy-btn');
                const oldText = btn.innerText;
                btn.innerText = 'Copied!';
                btn.style.backgroundColor = '#065f46';
                btn.style.borderColor = '#059669';
                setTimeout(() => {{
                    btn.innerText = oldText;
                    btn.style.backgroundColor = '';
                    btn.style.borderColor = '';
                }}, 2000);
            }}).catch(err => {{
                console.error('Could not copy text: ', err);
            }});
        }}
    </script>
</body>
</html>
"""
    return full_html


async def forward_request(request: Request, target_url: str):
    """
    Proxies the incoming request to the target origin server using HTTPX.
    """
    # Build target URL
    path = request.url.path
    query = request.url.query
    url = f"{target_url.rstrip('/')}{path}"
    if query:
        url += f"?{query}"

    # Prepare request details
    method = request.method
    headers = dict(request.headers)
    
    # Update Host header to match target URL host
    from urllib.parse import urlparse
    parsed = urlparse(target_url)
    headers["host"] = parsed.netloc

    body = await request.body()

    async with httpx.AsyncClient() as client:
        try:
            # We construct a request with the client and send it
            # We timeout after 30 seconds
            req = client.build_request(
                method,
                url,
                headers=headers,
                content=body,
                timeout=30.0
            )
            response = await client.send(req)
            return response
        except httpx.HTTPError as exc:
            logger.error(f"Error forwarding request to {url}: {exc}")
            return None


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def waf_proxy_route(request: Request, path: str):
    # Extract host domain
    host = request.headers.get("host", "").split(":")[0]
    
    # Create DB Session
    db = SessionLocal()
    site = None
    try:
        # Resolve target site from domain name
        # If running in local demo mode and host is localhost or 127.0.0.1, resolve the first site configured
        site = db.query(Site).filter(Site.domain == host).first()
        if not site and (host in ("localhost", "127.0.0.1") or host.startswith("192.168.")):
            site = db.query(Site).first() # Fallback for local testing
    except Exception as e:
        logger.error(f"Database site resolution failed: {e}")
        
    if not site:
        db.close()
        return Response(content="Site not configured in Web Security Suite WAF. Please add it to your dashboard.", status_code=404)

    # 1. Gather request data
    method = request.method
    request_path = request.url.path
    query_params = request.url.query
    headers_dict = dict(request.headers)
    
    body_bytes = await request.body()
    body_text = ""
    try:
        body_text = body_bytes.decode("utf-8")
    except Exception:
        body_text = "[Binary Content]"

    # 2. Run inspection
    is_blocked = False
    risk_score = 0
    matched_rules_list = []
    ai_reason = None
    event_id = None

    try:
        # Check signature rules
        inspection = rule_engine.inspect_request(
            method=method,
            path=request_path,
            headers=headers_dict,
            query=query_params,
            body=body_text
        )

        matched_rules_list = [r["name"] for r in inspection["rules"]]
        risk_score = inspection["risk_score"]

        # AI Layer (second pass): If matches rules but is borderline (30 to 70 risk score)
        # or if rule matches are SQLi / RCE / XSS, trigger verification
        if risk_score >= 30 and risk_score < 80:
            logger.info("Triggering Gemini WAF validation (risk borderline)...")
            ai_result = ai_provider.analyze_waf_request(
                method=method,
                path=request_path,
                headers=json.dumps(headers_dict),
                query=query_params,
                body=body_text[:2000],  # send first 2000 chars of body
                matched_rules=matched_rules_list
            )
            
            if ai_result["is_attack"]:
                risk_score = max(risk_score, ai_result["confidence"])
                ai_reason = ai_result["reasoning"]
            else:
                # AI determined it is a false positive
                risk_score = int(risk_score * 0.3)  # Reduce score
                ai_reason = f"AI classified request as benign: {ai_result['reasoning']}"

        elif risk_score >= 80:
            ai_reason = "High confidence rule match. Auto-blocked."

        # Decide on block
        if risk_score >= site.block_threshold:
            is_blocked = True

    except Exception as e:
        logger.error(f"WAF Engine exception: {e}")
        # Fail safe check
        if not settings.FAIL_SAFE_OPEN:
            is_blocked = True
            risk_score = 100
            ai_reason = f"System Error (Fail-Closed Mode Active): {e}"
        else:
            logger.warning("Fail safe open mode active: allowing traffic despite error")

    # 3. Log results and handle blocking
    ip_address = request.client.host if request.client else "127.0.0.1"

    if matched_rules_list or is_blocked or risk_score > 0:
        try:
            # Mask sensitive values in body/headers before saving log to PostgreSQL
            masked_body = body_text[:1000] # save truncated snippet
            
            from app.ai.ai_provider import redact_text
            masked_body = redact_text(masked_body)
            masked_headers = redact_text(json.dumps(headers_dict))

            # Store WafLog
            log_entry = WafLog(
                tenant_id=site.tenant_id,
                site_id=site.id,
                ip_address=ip_address,
                method=method,
                path=request_path,
                headers=masked_headers,
                query_params=query_params,
                body=masked_body,
                matched_rules=json.dumps(matched_rules_list),
                risk_score=risk_score,
                blocked=is_blocked if site.mode == "Block" else False,
                ai_reasoning=ai_reason
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            event_id = log_entry.id

            # Broadcast via WebSocket
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
            broadcast_waf_log(broadcast_payload)

        except Exception as e:
            logger.error(f"Failed to record WAF log: {e}")

    # 4. Handle Routing
    if is_blocked and site.mode == "Block":
        db.close()
        html_content = blocked_page_template.format(
            event_id=event_id or "N/A",
            ip_address=ip_address,
            reason=ai_reason or "Signature rule match",
            risk_score=risk_score
        )
        return HTMLResponse(content=html_content, status_code=403)

    # Proceed to proxy the request
    db.close()
    
    response = await forward_request(request, site.origin_url)
    if response is None:
        return Response(content="502 Bad Gateway - Web Security Suite Proxy could not connect to origin server.", status_code=502)

    # Build response to client
    # Extract headers to exclude hop-by-hop headers
    exclude_headers = [
        "content-encoding", "content-length", "transfer-encoding", 
        "connection", "keep-alive", "proxy-authenticate", 
        "proxy-authorization", "te", "trailers", "upgrade"
    ]
    resp_headers = {
        k: v for k, v in response.headers.items() 
        if k.lower() not in exclude_headers
    }
    
    # Intercept JSON response for browser clients (HTML format)
    content_type = response.headers.get("content-type", "")
    accept_header = request.headers.get("accept", "")
    if "application/json" in content_type and "text/html" in accept_header:
        try:
            response_json = response.json()
            html_content = render_json_visualizer(
                data=response_json,
                path=request_path,
                method=method,
                origin_url=site.origin_url
            )
            resp_headers["content-type"] = "text/html; charset=utf-8"
            return HTMLResponse(
                content=html_content,
                status_code=response.status_code,
                headers=resp_headers
            )
        except Exception as e:
            logger.error(f"Failed to render JSON visualizer: {e}")

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=resp_headers
    )
