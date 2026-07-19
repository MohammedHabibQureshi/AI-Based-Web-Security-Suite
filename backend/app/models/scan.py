from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base
from app.models.auth import generate_uuid

class Scan(Base):
    __tablename__ = "scans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    repo_url = Column(String(255), nullable=True)
    branch = Column(String(100), nullable=True)
    status = Column(String(20), default="Pending")  # Pending, Running, Completed, Failed
    score = Column(String(2), default="A")  # A, B, C, D, F
    total_findings = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="scans")
    findings = relationship("ScanFinding", back_populates="scan", cascade="all, delete-orphan")

class ScanFinding(Base):
    __tablename__ = "scan_findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    scan_id = Column(String(36), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(Text, nullable=False)
    line_number = Column(Integer, nullable=True)
    vulnerability_type = Column(String(100), nullable=False)  # e.g., SQL Injection, Hardcoded Secret
    severity = Column(String(20), nullable=False)            # Critical, High, Medium, Low
    plain_explanation = Column(Text, nullable=False)
    technical_explanation = Column(Text, nullable=False)
    suggested_fix_before = Column(Text, nullable=True)       # The vulnerability code chunk
    suggested_fix_after = Column(Text, nullable=True)        # The fixed code chunk
    hash = Column(String(32), index=True, nullable=False)     # For scanning cache diffing

    # Relationships
    tenant = relationship("Tenant", back_populates="scan_findings")
    scan = relationship("Scan", back_populates="findings")
