# scripts/init_database.py
"""Initialize the audit database"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so top-level imports (like `backend`) work
# when this script is executed directly (e.g. `py scripts\init_database.py`).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.audit.database import init_db
from config.logging_config import setup_logging


if __name__ == "__main__":
    setup_logging()
    print("Initializing database...")
    init_db()
    print("✅ Database initialized successfully!")