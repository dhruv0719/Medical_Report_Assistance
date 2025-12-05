# scripts/check_audit_logs.py
"""View recent audit logs"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.audit.database import get_db_session
from backend.audit.models import AuditLog
from sqlalchemy import desc

with get_db_session() as db:
    recent_logs = db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(10).all()
    
    print("="*60)
    print("RECENT AUDIT LOGS")
    print("="*60)
    
    for log in recent_logs:
        print(f"\n[{log.created_at}] {log.event_type.upper()}")
        print(f"  Session: {log.session_id[:16]}...")
        if log.input_data:
            print(f"  Input: {log.input_data}")
        if log.output_data:
            print(f"  Output: {log.output_data}")
    
    print(f"\n{'='*60}")
    print(f"Total logs: {db.query(AuditLog).count()}")