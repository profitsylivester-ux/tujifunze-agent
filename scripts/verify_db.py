import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "tujifunze_data.db"
conn = sqlite3.connect(DB)

print("=== S001 (Amina Hassan) — all scores across 3 terms ===")
rows = conn.execute(
    "SELECT term, subject, assignment_name, score, max_score "
    "FROM scores WHERE student_id = 'S001' "
    "ORDER BY assignment_date"
).fetchall()
for r in rows:
    print(f"  {r[0]}  {r[1]:<8} {r[2]:<25} {r[3]}/{r[4]}")

print()
print("=== S001 — attendance summary per term ===")
for term, status, count in conn.execute(
    "SELECT term, status, COUNT(*) FROM attendance "
    "WHERE student_id = 'S001' GROUP BY term, status ORDER BY term, status"
):
    print(f"  {term}  {status:<8} {count}")

print()
print("=== S001 — teacher observations ===")
for term, date, initials, note in conn.execute(
    "SELECT term, observation_date, teacher_initials, note "
    "FROM observations WHERE student_id = 'S001' ORDER BY observation_date"
):
    print(f"  [{term} | {date} | {initials}] {note[:90]}...")

conn.close()
