from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base
from app.models.auth import generate_uuid

class Site(Base):
    __tablename__ = "sites"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    domain = Column(String(255), unique=True, index=True, nullable=False)
    origin_url = Column(String(255), nullable=False)
    mode = Column(String(20), default="Block")  # Block, Monitor
    block_threshold = Column(Integer, default=50)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="sites")
    waf_logs = relationship("WafLog", back_populates="site", cascade="all, delete-orphan")
