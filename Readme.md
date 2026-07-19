# Web Security Suite (WAF + AI Vulnerability Scanner)

Web Security Suite is a production-grade, sellable SaaS + self-hosted security platform combining a real-time Web Application Firewall (WAF) proxy, an AI static code vulnerability scanner (SAST), and plain-English PDF security audit reporting.

Targeted at freelance developers, small agencies, and startups who need lightweight, easy-to-use, and clear security analysis without the high cost of Burp Suite Pro or the complex configuration of ModSecurity.

---

## 📊 Web Security Suite vs ModSecurity vs Burp Suite Pro

| Feature | ModSecurity | Burp Suite Pro | Web Security Suite |
| :--- | :--- | :--- | :--- |
| **Primary Use-Case** | Real-time signature WAF | Manual/automated pentesting | Real-time WAF + SAST Scanner |
| **Detection Engine** | Rules / Regex only | CVE Scanner / Heuristic | Rules/Regex + Context-Aware Gemini AI |
| **Remediation Details**| Log entry only | Technical CVE descriptions | **Plain-English explanations + Before/After code-level diffs** |
| **Reporting** | Syslog / JSON dump | XML/HTML CVE exports | **Client-ready professional PDF reports** |
| **Pricing** | Free (complex to set up) | $449/user/year (expensive) | Flexible Bring-Your-Own-Key / SaaS |

---

## 🏗️ Architecture Design

```
                     ┌──────────────────┐
                     │   User Browser   │
                     └────────┬─────────┘
                              │ HTTPS (e.g. Domain)
                              ▼
                      ┌──────────────────┐
                      │ Web Security Suite│
                      │ Proxy (Port 8080)│
                      └────────┬─────────┘
                               │
               ┌──────────────┴──────────────┐
               ▼ (Risk Check)                ▼ (Clean Proxy Route)
    ┌────────────────────┐         ┌────────────────────┐
    │  Rules + Gemini    │         │  Origin App Server │
    │  Sanitized Check   │         │ (e.g. localhost)   │
    └──────────┬─────────┘         └────────────────────┘
               │ (Log Save)
               ▼
    ┌────────────────────┐
    │  Postgres Database │ ◄──┐ (Get Metrics / Trigger Scans)
    └────────────────────┘    │
                              │
                     ┌────────┴─────────┐
                     │  FastAPI Server  │ ◄─── Websockets/REST
                     │   (Port 8000)    │
                     └────────▲─────────┘
                              │
                     ┌────────┴─────────┐
                     │  React Frontend  │
                     │    (Port 80)     │
                     └──────────────────┘
```

---

## ⚙️ Core Modules Built

1. **WAF Reverse Proxy (`app/waf/proxy.py`)**: Intercepts HTTP headers, body, query, and path; matches regex signatures; triggers Gemini context check if risk is borderline (30-70); blocks threats above threshold with a premium "Access Denied" page.
2. **AI Vulnerability Scanner (`app/scanner/static_scanner.py`)**: Identifies languages/frameworks; runs static pattern audits; checks previous scan hashes (MD5) to avoid redundant AI calls; queries Gemini for security confirmation and code fixes.
3. **WeasyPrint PDF Generator (`app/reports/pdf_generator.py`)**: Combines dynamic HTML template layouts, inline SVG pie/line charts, and renders detailed audits. Automatically falls back to a clean print-ready HTML page if gtk libraries are missing.
4. **Multi-Tenant REST API & Websockets (`app/api/`)**: Provides JWT auth, site rules dashboard, scan triggers, real-time alert broadcasts to the frontend.
5. **Express/Python SDK Middleware (`sdk/`)**: Stubs enabling developers to run inline threat inspections on internal APIs without routing through the proxy.

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Google Gemini API Key (Optional; runs in mock demo mode if empty)

### 🐳 Run using Docker Compose (Self-Hosted / Production)
1. Rename `.env.example` to `.env` and fill in your Gemini key:
   ```bash
   cp .env.example .env
   ```
2. Build and launch all containers:
   ```bash
   docker-compose up -d --build
   ```
3. Access Web Security Suite:
   - **Frontend Dashboard**: [http://localhost](http://localhost) (Register an admin account first)
   - **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **WAF Proxy Target**: Point your DNS record or headers to [http://localhost:8080](http://localhost:8080)

---

## 🛠️ Local Development (Fallbacks Enabled)

To develop locally without Postgres/Redis docker requirements:
1. Install Python requirements in a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Copy settings and run:
   ```bash
   # Set environment overrides
   export DATABASE_URL=sqlite:///./sentinelai.db
   export REDIS_URL=redis://localhost:6379/0  # SQLite db will automatically initialize on boot!
   
   # Start Backend Server
   uvicorn app.main:app --reload --port 8000
   
   # Start WAF Proxy (In a separate terminal)
   python run_waf.py
   ```
3. Run signature engine verification tests:
   ```bash
   pip install pyyaml
   python tests/test_rules.py
   ```

---

## 📦 SDK Middleware Integration Example

### Node.js / Express Middleware
```javascript
const express = require('express');
const sentinelaiMiddleware = require('./sdk/node');

const app = express();
app.use(express.json());

// Protect API with Web Security Suite
app.use(sentinelaiMiddleware({
  domain: 'myapi.company.com',
  portalUrl: 'http://localhost:8000', // Core Web Security Suite backend
  failSafeOpen: true
}));

app.get('/api/data', (req, res) => {
  res.json({ message: "Access Granted" });
});
app.listen(8001);
```
