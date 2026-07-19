from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base
from app.models.auth import generate_uuid

class WafLog(Base):
    __tablename__ = "waf_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    ip_address = Column(String(45), nullable=False)  # Supports IPv6 lengths
    method = Column(String(10), nullable=False)
    path = Column(Text, nullable=False)
    headers = Column(Text, nullable=True)  # JSON-serialized request headers
    query_params = Column(Text, nullable=True)
    body = Column(Text, nullable=True)     # Redacted request body snippet
    matched_rules = Column(Text, nullable=True) # JSON-serialized list of matched regex rule names
    risk_score = Column(Integer, default=0)
    blocked = Column(Boolean, default=False)
    ai_reasoning = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="waf_logs")
    site = relationship("Site", back_populates="waf_logs")
