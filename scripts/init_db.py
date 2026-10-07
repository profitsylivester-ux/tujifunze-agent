"""
Seed tujifunze_data.db with realistic synthetic student data
across 3 academic terms for multiple students.

Creates 4 tables:
  - students       (roster)
  - scores         (per-assignment academic records)
  - attendance     (per-day attendance records)
  - observations   (qualitative teacher notes)
"""

import sqlite3
from pathlib import Path

# Resolve DB path relative to this script so it works from anywhere
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tujifunze_data.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


STUDENTS = [
    # (student_id, full_name, grade_level, cohort_year)
    ("S001", "Amina Hassan",      7, 2024),
    ("S002", "Brian Otieno",      7, 2024),
    ("S003", "Cynthia Wanjiru",   7, 2024),
    ("S004", "David Mwangi",      7, 2024),
    ("S005", "Esther Njeri",      7, 2024),
    ("S006", "Farid Abdullah",    7, 2024),
]

# (student_id, term, subject, assignment_name, assignment_date, score, max_score)
SCORES = [
    # ---------- Term 1 2024 ----------
    ("S001", "2024-T1", "Math",    "Fractions Quiz",        "2024-02-05", 14, 20),
    ("S001", "2024-T1", "Math",    "Mid-Term Test",         "2024-02-28", 16, 25),
    ("S001", "2024-T1", "English", "Reading Comp",          "2024-02-10", 18, 20),
    ("S001", "2024-T1", "Science", "Plant Cells Worksheet", "2024-03-01", 15, 20),

    ("S002", "2024-T1", "Math",    "Fractions Quiz",        "2024-02-05", 10, 20),
    ("S002", "2024-T1", "Math",    "Mid-Term Test",         "2024-02-28", 12, 25),
    ("S002", "2024-T1", "English", "Reading Comp",          "2024-02-10", 14, 20),
    ("S002", "2024-T1", "Science", "Plant Cells Worksheet", "2024-03-01", 11, 20),

    ("S003", "2024-T1", "Math",    "Fractions Quiz",        "2024-02-05", 17, 20),
    ("S003", "2024-T1", "Math",    "Mid-Term Test",         "2024-02-28", 20, 25),
    ("S003", "2024-T1", "English", "Reading Comp",          "2024-02-10", 19, 20),
    ("S003", "2024-T1", "Science", "Plant Cells Worksheet", "2024-03-01", 18, 20),

    ("S004", "2024-T1", "Math",    "Fractions Quiz",        "2024-02-05",  8, 20),
    ("S004", "2024-T1", "Math",    "Mid-Term Test",         "2024-02-28", 10, 25),
    ("S004", "2024-T1", "English", "Reading Comp",          "2024-02-10", 12, 20),
    ("S004", "2024-T1", "Science", "Plant Cells Worksheet", "2024-03-01",  9, 20),

    ("S005", "2024-T1", "Math",    "Fractions Quiz",        "2024-02-05", 15, 20),
    ("S005", "2024-T1", "Math",    "Mid-Term Test",         "2024-02-28", 18, 25),
    ("S005", "2024-T1", "English", "Reading Comp",          "2024-02-10", 17, 20),
    ("S005", "2024-T1", "Science", "Plant Cells Worksheet", "2024-03-01", 16, 20),

    ("S006", "2024-T1", "Math",    "Fractions Quiz",        "2024-02-05", 12, 20),
    ("S006", "2024-T1", "Math",    "Mid-Term Test",         "2024-02-28", 13, 25),
    ("S006", "2024-T1", "English", "Reading Comp",          "2024-02-10", 16, 20),
    ("S006", "2024-T1", "Science", "Plant Cells Worksheet", "2024-03-01", 14, 20),

    # ---------- Term 2 2024 ----------
    ("S001", "2024-T2", "Math",    "Algebra Intro Quiz",    "2024-05-06", 16, 20),
    ("S001", "2024-T2", "Math",    "Mid-Term Test",         "2024-06-03", 19, 25),
    ("S001", "2024-T2", "English", "Essay Draft",           "2024-05-15", 17, 20),
    ("S001", "2024-T2", "Science", "Acids and Bases Lab",   "2024-06-10", 18, 20),

    ("S002", "2024-T2", "Math",    "Algebra Intro Quiz",    "2024-05-06", 11, 20),
    ("S002", "2024-T2", "Math",    "Mid-Term Test",         "2024-06-03", 14, 25),
    ("S002", "2024-T2", "English", "Essay Draft",           "2024-05-15", 15, 20),
    ("S002", "2024-T2", "Science", "Acids and Bases Lab",   "2024-06-10", 13, 20),

    ("S003", "2024-T2", "Math",    "Algebra Intro Quiz",    "2024-05-06", 18, 20),
    ("S003", "2024-T2", "Math",    "Mid-Term Test",         "2024-06-03", 22, 25),
    ("S003", "2024-T2", "English", "Essay Draft",           "2024-05-15", 18, 20),
    ("S003", "2024-T2", "Science", "Acids and Bases Lab",   "2024-06-10", 19, 20),

    ("S004", "2024-T2", "Math",    "Algebra Intro Quiz",    "2024-05-06", 10, 20),
    ("S004", "2024-T2", "Math",    "Mid-Term Test",         "2024-06-03", 13, 25),
    ("S004", "2024-T2", "English", "Essay Draft",           "2024-05-15", 14, 20),
    ("S004", "2024-T2", "Science", "Acids and Bases Lab",   "2024-06-10", 12, 20),

    ("S005", "2024-T2", "Math",    "Algebra Intro Quiz",    "2024-05-06", 17, 20),
    ("S005", "2024-T2", "Math",    "Mid-Term Test",         "2024-06-03", 20, 25),
    ("S005", "2024-T2", "English", "Essay Draft",           "2024-05-15", 19, 20),
    ("S005", "2024-T2", "Science", "Acids and Bases Lab",   "2024-06-10", 18, 20),

    ("S006", "2024-T2", "Math",    "Algebra Intro Quiz",    "2024-05-06", 13, 20),
    ("S006", "2024-T2", "Math",    "Mid-Term Test",         "2024-06-03", 15, 25),
    ("S006", "2024-T2", "English", "Essay Draft",           "2024-05-15", 16, 20),
    ("S006", "2024-T2", "Science", "Acids and Bases Lab",   "2024-06-10", 15, 20),

    # ---------- Term 3 2024 ----------
    ("S001", "2024-T3", "Math",    "Geometry Quiz",         "2024-09-09", 18, 20),
    ("S001", "2024-T3", "Math",    "End-Term Exam",         "2024-11-04", 21, 25),
    ("S001", "2024-T3", "English", "Poetry Analysis",       "2024-09-20", 19, 20),
    ("S001", "2024-T3", "Science", "Ecosystems Project",    "2024-10-15", 17, 20),

    ("S002", "2024-T3", "Math",    "Geometry Quiz",         "2024-09-09", 13, 20),
    ("S002", "2024-T3", "Math",    "End-Term Exam",         "2024-11-04", 16, 25),
    ("S002", "2024-T3", "English", "Poetry Analysis",       "2024-09-20", 16, 20),
    ("S002", "2024-T3", "Science", "Ecosystems Project",    "2024-10-15", 14, 20),

    ("S003", "2024-T3", "Math",    "Geometry Quiz",         "2024-09-09", 19, 20),
    ("S003", "2024-T3", "Math",    "End-Term Exam",         "2024-11-04", 23, 25),
    ("S003", "2024-T3", "English", "Poetry Analysis",       "2024-09-20", 20, 20),
    ("S003", "2024-T3", "Science", "Ecosystems Project",    "2024-10-15", 19, 20),

    ("S004", "2024-T3", "Math",    "Geometry Quiz",         "2024-09-09", 11, 20),
    ("S004", "2024-T3", "Math",    "End-Term Exam",         "2024-11-04", 15, 25),
    ("S004", "2024-T3", "English", "Poetry Analysis",       "2024-09-20", 15, 20),
    ("S004", "2024-T3", "Science", "Ecosystems Project",    "2024-10-15", 14, 20),

    ("S005", "2024-T3", "Math",    "Geometry Quiz",         "2024-09-09", 19, 20),
    ("S005", "2024-T3", "Math",    "End-Term Exam",         "2024-11-04", 22, 25),
    ("S005", "2024-T3", "English", "Poetry Analysis",       "2024-09-20", 20, 20),
    ("S005", "2024-T3", "Science", "Ecosystems Project",    "2024-10-15", 19, 20),

    ("S006", "2024-T3", "Math",    "Geometry Quiz",         "2024-09-09", 14, 20),
    ("S006", "2024-T3", "Math",    "End-Term Exam",         "2024-11-04", 17, 25),
    ("S006", "2024-T3", "English", "Poetry Analysis",       "2024-09-20", 17, 20),
    ("S006", "2024-T3", "Science", "Ecosystems Project",    "2024-10-15", 16, 20),
]

# (student_id, term, school_day, status)  status: present | absent | late
ATTENDANCE = []
import datetime as _dt

def _weekdays(start_iso, weeks):
    """Yield weekday date strings starting from start_iso for N weeks."""
    start = _dt.date.fromisoformat(start_iso)
    count = 0
    d = start
    while count < weeks * 5:
        if d.weekday() < 5:
            yield d.isoformat()
            count += 1
        d += _dt.timedelta(days=1)

# Term 1 attendance (Feb-Mar 2024)
for sid, absent_days in [("S001", []), ("S002", ["2024-02-13", "2024-03-05"]),
                          ("S003", []), ("S004", ["2024-02-20", "2024-02-27", "2024-03-12"]),
                          ("S005", []), ("S006", ["2024-02-14"])]:
    for d in _weekdays("2024-02-05", 6):
        if d in absent_days:
            ATTENDANCE.append((sid, "2024-T1", d, "absent"))
        elif d in ["2024-02-15", "2024-03-01"]:
            ATTENDANCE.append((sid, "2024-T1", d, "late"))
        else:
            ATTENDANCE.append((sid, "2024-T1", d, "present"))

# Term 2 attendance (May-Jun 2024)
for sid, absent_days in [("S001", []), ("S002", ["2024-05-14", "2024-06-04"]),
                          ("S003", []), ("S004", ["2024-05-21", "2024-06-11", "2024-06-18"]),
                          ("S005", ["2024-05-22"]), ("S006", [])]:
    for d in _weekdays("2024-05-06", 6):
        if d in absent_days:
            ATTENDANCE.append((sid, "2024-T2", d, "absent"))
        elif d in ["2024-05-17", "2024-06-07"]:
            ATTENDANCE.append((sid, "2024-T2", d, "late"))
        else:
            ATTENDANCE.append((sid, "2024-T2", d, "present"))

# Term 3 attendance (Sep-Nov 2024)
for sid, absent_days in [("S001", []), ("S002", ["2024-09-17"]),
                          ("S003", []), ("S004", ["2024-09-24", "2024-10-08", "2024-10-22", "2024-11-05"]),
                          ("S005", []), ("S006", ["2024-10-01"])]:
    for d in _weekdays("2024-09-09", 8):
        if d in absent_days:
            ATTENDANCE.append((sid, "2024-T3", d, "absent"))
        elif d in ["2024-09-13", "2024-10-11"]:
            ATTENDANCE.append((sid, "2024-T3", d, "late"))
        else:
            ATTENDANCE.append((sid, "2024-T3", d, "present"))

# (student_id, term, observation_date, teacher_initials, note)
OBSERVATIONS = [
    ("S001", "2024-T1", "2024-02-20", "JM",
     "Amina is quietly persistent. When she does not understand a fraction problem, she re-reads "
     "the worked example before asking. By late February she was explaining her steps to a neighbour."),
    ("S001", "2024-T2", "2024-05-20", "JM",
     "Amina has grown noticeably in confidence during group work. She now volunteers to present "
     "her group's answers. Her written English is careful and structured."),
    ("S001", "2024-T3", "2024-10-10", "JM",
     "Amina consistently helps classmates without being asked. In math she is now attempting the "
     "challenge questions at the bottom of each worksheet before moving on."),

    ("S002", "2024-T1", "2024-02-22", "JM",
     "Brian is engaged in class discussion but rushes written work. Many errors are careless, "
     "not conceptual. Attendance has been interrupted by two absences."),
    ("S002", "2024-T2", "2024-05-22", "JM",
     "Brian is showing improved patience with written tasks when given a checklist. Still loses "
     "focus on longer tasks. Missing two more days did not help continuity."),
    ("S002", "2024-T3", "2024-10-12", "JM",
     "Clear upward trend in Brian's written work this term. He is checking answers before handing "
     "in. Attendance is steadier. He responds well to short, specific feedback."),

    ("S003", "2024-T1", "2024-02-23", "JM",
     "Cynthia is a strong all-round performer. She finishes early and uses the extra time to read "
     "ahead. Occasionally bored during revision lessons."),
    ("S003", "2024-T2", "2024-05-24", "JM",
     "Cynthia continues to excel. She has taken on a peer-tutoring role informally, which suits "
     "her. I would like to stretch her with independent projects."),
    ("S003", "2024-T3", "2024-10-14", "JM",
     "Cynthia's science project on ecosystems was exceptional. She is ready for above-grade-level "
     "extension work in math and science."),

    ("S004", "2024-T1", "2024-02-26", "JM",
     "David struggles with foundational number work and has missed several days. He avoids "
     "volunteering answers. One-to-one support seems to help but has been inconsistent."),
    ("S004", "2024-T2", "2024-05-27", "JM",
     "David is beginning to attempt problems independently. His attendance remains the biggest "
     "obstacle — the gaps in his learning are visible when new topics build on missed ones."),
    ("S004", "2024-T3", "2024-10-15", "JM",
     "Encouraging improvement in David's math when he is present. He responds very well to small "
     "group work. Attendance this term is again the main concern."),

    ("S005", "2024-T1", "2024-02-27", "JM",
     "Esther is a steady, reliable worker. Rarely the first to speak, but her written answers are "
     "thoughtful. Perfect attendance so far."),
    ("S005", "2024-T2", "2024-05-28", "JM",
     "Esther has started participating more in class discussion. Her essay draft showed careful "
     "structure and vivid description. She is reliable in group tasks."),
    ("S005", "2024-T3", "2024-10-16", "JM",
     "Esther is now one of the most consistent performers in the class. Her end-of-term exam was "
     "her strongest yet. Continued steady progress."),

    ("S006", "2024-T1", "2024-02-28", "JM",
     "Farid is curious and asks good questions but rushes to finish first. His answers show he "
     "understands more than his scores suggest."),
    ("S006", "2024-T2", "2024-05-29", "JM",
     "Farid's accuracy is improving as he slows down. He is beginning to check his own work. One "
     "absence in Term 2."),
    ("S006", "2024-T3", "2024-10-17", "JM",
     "Farid has become noticeably more careful. His geometry work was neat and accurate. Good "
     "trajectory across the year."),
]


def init_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed existing database at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE students (
            student_id   TEXT PRIMARY KEY,
            full_name    TEXT NOT NULL,
            grade_level  INTEGER NOT NULL,
            cohort_year  INTEGER NOT NULL
        );

        CREATE TABLE scores (
            record_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id       TEXT NOT NULL,
            term             TEXT NOT NULL,
            subject          TEXT NOT NULL,
            assignment_name  TEXT NOT NULL,
            assignment_date  TEXT NOT NULL,
            score            REAL NOT NULL,
            max_score        REAL NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        );

        CREATE TABLE attendance (
            record_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id   TEXT NOT NULL,
            term         TEXT NOT NULL,
            school_day   TEXT NOT NULL,
            status       TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        );

        CREATE TABLE observations (
            record_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id        TEXT NOT NULL,
            term              TEXT NOT NULL,
            observation_date  TEXT NOT NULL,
            teacher_initials  TEXT NOT NULL,
            note              TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        );

        CREATE INDEX idx_scores_student       ON scores(student_id);
        CREATE INDEX idx_scores_student_term  ON scores(student_id, term);
        CREATE INDEX idx_attendance_student   ON attendance(student_id);
        CREATE INDEX idx_observations_student ON observations(student_id);
    """)

    cur.executemany(
        "INSERT INTO students (student_id, full_name, grade_level, cohort_year) VALUES (?, ?, ?, ?)",
        STUDENTS,
    )
    cur.executemany(
        "INSERT INTO scores (student_id, term, subject, assignment_name, assignment_date, score, max_score) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        SCORES,
    )
    cur.executemany(
        "INSERT INTO attendance (student_id, term, school_day, status) VALUES (?, ?, ?, ?)",
        ATTENDANCE,
    )
    cur.executemany(
        "INSERT INTO observations (student_id, term, observation_date, teacher_initials, note) "
        "VALUES (?, ?, ?, ?, ?)",
        OBSERVATIONS,
    )

    conn.commit()

    print(f"Database created at: {DB_PATH}")
    print(f"  students:     {cur.execute('SELECT COUNT(*) FROM students').fetchone()[0]}")
    print(f"  scores:       {cur.execute('SELECT COUNT(*) FROM scores').fetchone()[0]}")
    print(f"  attendance:   {cur.execute('SELECT COUNT(*) FROM attendance').fetchone()[0]}")
    print(f"  observations: {cur.execute('SELECT COUNT(*) FROM observations').fetchone()[0]}")
    conn.close()


if __name__ == "__main__":
    init_db()
