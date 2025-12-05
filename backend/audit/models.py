# backend/audit/models.py
"""
SQLAlchemy models for audit logging.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime
# IMPORTANT: Import Base from database.py, don't create a new one!
from backend.audit.database import Base

class AuditLog(Base):
    """Audit log table for tracking all system interactions"""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    event_type = Column(String(50), index=True)  # 'upload', 'parse', 'llm_call', etc.
    session_id = Column(String(64), index=True)
    user_id = Column(String(64), nullable=True)
    
    # Event data (JSON)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    
    # Error tracking
    error = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type='{self.event_type}', created_at='{self.created_at}')>"

__all__ = [
    "AuditLog",
]