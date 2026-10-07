"""
Database connection helper for the Tujifunze agent tools.
All tools import get_connection() from here — single source of truth for the DB path.
"""

import sqlite3
from pathlib import Path


# Path to the SQLite database, resolved relative to the project root.
# This file lives at: <project_root>/tools/db.py
# So parent.parent = project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "tujifunze_data.db"


def get_connection() -> sqlite3.Connection:
    """
    Open a connection to the Tujifunze SQLite database.

    Rows come back as sqlite3.Row objects so we can access columns by name
    (e.g., row["score"] instead of row[3]).
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. "
            f"Run: python scripts/init_db.py"
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
