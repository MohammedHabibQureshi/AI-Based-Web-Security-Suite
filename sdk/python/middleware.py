"""
Web Security Suite Python WSGI / ASGI Middleware Stub
"""
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger("WebSecuritySuite-SDK")

class SentinelMiddleware:
    def __init__(self, app, domain: str, portal_url: str = "http://localhost:8000", fail_safe_open: bool = True):
        self.app = app
        self.domain = domain
        self.portal_url = portal_url
        self.fail_safe_open = fail_safe_open

    def __call__(self, environ, start_response):
        # 1. Extract request details
        method = environ.get("REQUEST_METHOD", "GET")
        path = environ.get("PATH_INFO", "")
        query = environ.get("QUERY_STRING", "")
        ip_addr = environ.get("REMOTE_ADDR", "127.0.0.1")

        # Get Headers
        headers = {}
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                header_name = key[5:].replace("_", "-").lower()
                headers[header_name] = value

        # Try to read body
        body = ""
        try:
            content_length = int(environ.get("CONTENT_LENGTH", 0))
            if content_length > 0:
                body_bytes = environ["wsgi.input"].read(content_length)
                body = body_bytes.decode("utf-8", errors="ignore")
                # Put body back to input stream for application consumption
                import io
                environ["wsgi.input"] = io.BytesIO(body_bytes)
        except Exception:
            pass

        # 2. Build SDK API Request
        payload = {
            "domain": self.domain,
            "method": method,
            "path": path,
            "headers": headers,
            "query_params": query,
            "body": body,
            "ip_address": ip_addr
        }
        
        req_data = json.dumps(payload).encode("utf-8")
        req_url = f"{self.portal_url.rstrip('/')}/api/waf/check"
        
        req = urllib.request.Request(
            req_url, 
            data=req_data, 
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        blocked = False
        reason = "Detection Failure"

        try:
            # Short timeout of 1.5 seconds
            with urllib.request.urlopen(req, timeout=1.5) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                blocked = res_data.get("blocked", False)
                reason = res_data.get("reason", "")
        except urllib.error.URLError as e:
            logger.error(f"[Web Security Suite] Threat server check failed: {e}")
            if not self.fail_safe_open:
                blocked = True
        except Exception as e:
            logger.error(f"[Web Security Suite] Unknown middleware error: {e}")
            if not self.fail_safe_open:
                blocked = True

        # 3. Block response if flagged
        if blocked:
            status = "403 Forbidden"
            response_headers = [("Content-type", "text/html")]
            start_response(status, response_headers)
            
            html_content = f"""
            <html>
              <body style="background: #020617; color: #f1f5f9; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0;">
                <div style="text-align: center; border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; padding: 30px; background: #0f172a; max-width: 450px;">
                  <h1 style="color: #ef4444;">Request Blocked</h1>
                  <p style="color: #94a3b8;">Blocked by Web Security Suite Python WSGI Middleware.</p>
                  <div style="font-size: 12px; font-family: monospace; background: #020617; padding: 10px; border-radius: 6px; word-break: break-all;">
                    Reason: {reason}
                  </div>
                </div>
              </body>
            </html>
            """
            return [html_content.encode("utf-8")]

        # Proceed to downstream app
        return self.app(environ, start_response)
