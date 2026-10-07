import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "tujifunze_data.db"
conn = sqlite3.connect(DB)

conn.executescript("""
    CREATE TABLE IF NOT EXISTS flagged_patterns (
        pattern_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id        TEXT NOT NULL,
        pattern_type      TEXT NOT NULL,
        description       TEXT NOT NULL,
        source_citations  TEXT NOT NULL,
        created_at        TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    );

    CREATE INDEX IF NOT EXISTS idx_patterns_student ON flagged_patterns(student_id);
""")
conn.commit()

n = conn.execute("SELECT COUNT(*) FROM flagged_patterns").fetchone()[0]
print(f"flagged_patterns table ready. Rows: {n}")
conn.close()
