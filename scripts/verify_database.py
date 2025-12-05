# scripts/verify_database.py
"""Verify database was created correctly"""

import sys
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

db_path = PROJECT_ROOT / "audit.db"

print(f"Checking database: {db_path}")
print(f"Exists: {db_path.exists()}")

if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"\nTables: {[t[0] for t in tables]}")
    
    if any('audit_logs' in t for t in tables):
        print("\n✅ audit_logs table exists!")
        
        # Show schema
        cursor.execute("PRAGMA table_info(audit_logs);")
        columns = cursor.fetchall()
        
        print("\nColumns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    else:
        print("\n❌ audit_logs table NOT FOUND!")
    
    conn.close()
else:
    print("\n❌ Database file doesn't exist!")