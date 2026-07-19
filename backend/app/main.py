import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import engine, Base
from app.api import auth, sites, scans, logs, dashboard, reports, waf

# Initialize Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("WebSecuritySuite")

# Create Database tables on startup (especially helpful for local SQLite development)
try:
    logger.info("Initializing database schemas...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schemas initialized successfully.")
except Exception as e:
    logger.error(f"Error initializing database tables: {e}")

app = FastAPI(
    title="Web Security Suite API",
    description="Backend API for Web Security Suite WAF & Static Code Vulnerability Scanner Suite",
    version="1.0.0"
)

# CORS Configuration
# Allow frontend React connections
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "*"  # Allow all for deployment ease, narrow down in prod env
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Content-Disposition"],
)

# Include Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(sites.router, prefix="/api/sites", tags=["WAF Sites"])
app.include_router(logs.router, prefix="/api/logs", tags=["WAF Logs"])
app.include_router(scans.router, prefix="/api/scans", tags=["Vulnerability Scans"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(reports.router, prefix="/api/reports", tags=["PDF Reports"])
app.include_router(waf.router, prefix="/api/waf", tags=["WAF Engine"])

@app.get("/")
def home():
    return {
        "status": "online",
        "service": "Web Security Suite",
        "version": "1.0.0"
    }
