import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "tujifunze_data.db"
conn = sqlite3.connect(DB)

conn.executescript("""
    CREATE TABLE IF NOT EXISTS draft_reports (
        report_id          INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id         TEXT NOT NULL,
        summary_text       TEXT NOT NULL,
        citations          TEXT NOT NULL,
        status             TEXT NOT NULL DEFAULT 'draft',
        created_at         TEXT NOT NULL DEFAULT (datetime('now')),
        approved_at        TEXT,
        approved_by        TEXT,
        final_text         TEXT,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    );

    CREATE INDEX IF NOT EXISTS idx_reports_student ON draft_reports(student_id);
    CREATE INDEX IF NOT EXISTS idx_reports_status  ON draft_reports(status);
""")
conn.commit()

n = conn.execute("SELECT COUNT(*) FROM draft_reports").fetchone()[0]
print(f"draft_reports table ready. Rows: {n}")
conn.close()
