import uvicorn
import sys
import os

# Add parent directory to path so app can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

if __name__ == "__main__":
    port = int(os.getenv("WAF_PROXY_PORT", settings.WAF_PROXY_PORT))
    print(f"Starting Web Security Suite WAF Proxy on port {port}...")
    uvicorn.run("app.waf.proxy:app", host="0.0.0.0", port=port, log_level="info")
