# backend/audit/audit_logger.py
"""
Audit logging functionality for compliance and tracking.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.audit.models import AuditLog
from backend.audit.database import get_db_session
from config.logging_config import get_logger

logger = get_logger(__name__)

class AuditLogger:
    """Handles audit logging for compliance"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
    
    def log_event(
        self,
        event_type: str,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        Log an audit event to the database.
        
        Args:
            event_type: Type of event (upload, parse, llm_call, etc.)
            input_data: Input data (will be JSON serialized)
            output_data: Output data (will be JSON serialized)
            metadata: Additional metadata
            user_id: User identifier (if applicable)
            error: Error message (if applicable)
        """
        try:
            with get_db_session() as db:
                audit_entry = AuditLog(
                    created_at=datetime.utcnow(),
                    event_type=event_type,
                    session_id=self.session_id,
                    user_id=user_id,
                    input_data=input_data,
                    output_data=output_data,
                    metadata_=metadata,
                    error=error
                )
                
                db.add(audit_entry)
                db.commit()
                
                logger.info(f"Audit log created: {event_type} (session: {self.session_id})")
                
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
    
    # Convenience methods for specific events
    
    def log_upload(self, filename: str, file_hash: str, file_size: int):
        """Log file upload event"""
        self.log_event(
            event_type="upload",
            input_data={
                "filename": filename,
                "file_hash": file_hash,
                "file_size": file_size
            }
        )
    
    def log_extraction(self, method: str, char_count: int, duration: float):
        """Log text extraction event"""
        self.log_event(
            event_type="extraction",
            output_data={
                "method": method,
                "char_count": char_count,
                "duration_seconds": duration
            }
        )
    
    def log_parse(self, test_count: int, abnormal_count: int):
        """Log parsing event"""
        self.log_event(
            event_type="parse",
            output_data={
                "test_count": test_count,
                "abnormal_count": abnormal_count
            }
        )
    
    def log_llm_call(self, model: str, prompt_length: int, response_length: int, duration: float):
        """Log LLM API call"""
        self.log_event(
            event_type="llm_call",
            metadata={
                "model": model,
                "prompt_length": prompt_length,
                "response_length": response_length,
                "duration_seconds": duration
            }
        )
    
    def log_alert(self, alert_level: str, test_name: str, value: str):
        """Log safety alert"""
        self.log_event(
            event_type="alert",
            output_data={
                "level": alert_level,
                "test_name": test_name,
                "value": value
            }
        )
    
    def log_error(self, error_type: str, error_message: str):
        """Log error event"""
        self.log_event(
            event_type="error",
            error=f"{error_type}: {error_message}"
        )


__all__ = [
    "AuditLogger",
]