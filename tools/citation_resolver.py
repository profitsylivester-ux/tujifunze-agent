"""
Citation resolver.

Turns opaque citation IDs like "score:14" or "observation:3" into
human-readable text that a teacher or guardian can understand.

Example:
    resolve_citations(conn, "S001", ["score:1", "observation:2"])
    ->
    [
        "Fractions Quiz (2024-02-05) - Term 1 Math, scored 14/20",
        "Teacher note (2024-02-20, JM): Amina is quietly persistent...",
    ]
"""

from typing import Any
from tools.db import get_connection


def resolve_citations(
    student_id: str,
    citations: list[str],
) -> list[dict[str, Any]]:
    """
    Resolve a list of citation IDs into readable descriptors.

    Returns a list of dicts, each with:
        - id: the original citation ID
        - kind: "score" | "observation" | "attendance" | "pattern" | "unknown"
        - text: a human-readable single-line description
        - detail: a dict with the raw fields (for structured PDF rendering)

    Unknown or invalid citations are returned with kind="unknown" and a
    fallback text, so the caller can still show something instead of crashing.
    """
    conn = get_connection()
    try:
        results = []
        for c in citations:
            results.append(_resolve_one(conn, student_id, c))
        return results
    finally:
        conn.close()


def _resolve_one(conn, student_id: str, citation: str) -> dict[str, Any]:
    if not isinstance(citation, str) or ":" not in citation:
        return {
            "id": citation,
            "kind": "unknown",
            "text": f"Unrecognized citation: {citation}",
            "detail": {},
        }

    kind, _, raw_id = citation.partition(":")

    if kind == "score":
        return _resolve_score(conn, student_id, citation, raw_id)
    if kind == "observation":
        return _resolve_observation(conn, student_id, citation, raw_id)
    if kind == "attendance":
        return _resolve_attendance(conn, student_id, citation, raw_id)
    if kind == "pattern":
        return _resolve_pattern(conn, student_id, citation, raw_id)

    return {
        "id": citation,
        "kind": "unknown",
        "text": f"Unknown citation type: {kind}",
        "detail": {},
    }


def _resolve_score(conn, student_id, citation, raw_id):
    row = conn.execute(
        "SELECT term, subject, assignment_name, assignment_date, score, max_score "
        "FROM scores WHERE record_id = ? AND student_id = ?",
        (raw_id, student_id),
    ).fetchone()
    if row is None:
        return {"id": citation, "kind": "score", "text": f"Missing score record {raw_id}", "detail": {}}

    # Pretty term label, e.g. "2024-T1" -> "Term 1"
    term_label = row["term"]
    if "-T" in term_label:
        year, _, term_num = term_label.partition("-T")
        term_label = f"Term {term_num} {year}"

    detail = {
        "term": row["term"],
        "term_label": term_label,
        "subject": row["subject"],
        "assignment_name": row["assignment_name"],
        "assignment_date": row["assignment_date"],
        "score": row["score"],
        "max_score": row["max_score"],
    }
    text = (
        f"{row['assignment_name']} ({row['assignment_date']}) - "
        f"{term_label} {row['subject']}, scored "
        f"{_fmt_num(row['score'])}/{_fmt_num(row['max_score'])}"
    )
    return {"id": citation, "kind": "score", "text": text, "detail": detail}


def _resolve_observation(conn, student_id, citation, raw_id):
    row = conn.execute(
        "SELECT term, observation_date, teacher_initials, note "
        "FROM observations WHERE record_id = ? AND student_id = ?",
        (raw_id, student_id),
    ).fetchone()
    if row is None:
        return {"id": citation, "kind": "observation", "text": f"Missing observation {raw_id}", "detail": {}}

    term_label = row["term"]
    if "-T" in term_label:
        year, _, term_num = term_label.partition("-T")
        term_label = f"Term {term_num} {year}"

    # Truncate the note to keep the PDF tidy
    note = row["note"]
    snippet = note if len(note) <= 160 else note[:157] + "..."

    detail = {
        "term": row["term"],
        "term_label": term_label,
        "date": row["observation_date"],
        "teacher_initials": row["teacher_initials"],
        "note": note,
        "snippet": snippet,
    }
    text = f"Teacher note ({row['observation_date']}, {row['teacher_initials']}): {snippet}"
    return {"id": citation, "kind": "observation", "text": text, "detail": detail}


def _resolve_attendance(conn, student_id, citation, raw_id):
    row = conn.execute(
        "SELECT term, school_day, status "
        "FROM attendance WHERE record_id = ? AND student_id = ?",
        (raw_id, student_id),
    ).fetchone()
    if row is None:
        return {"id": citation, "kind": "attendance", "text": f"Missing attendance record {raw_id}", "detail": {}}

    detail = {
        "term": row["term"],
        "school_day": row["school_day"],
        "status": row["status"],
    }
    text = f"Attendance ({row['school_day']}): {row['status']}"
    return {"id": citation, "kind": "attendance", "text": text, "detail": detail}


def _resolve_pattern(conn, student_id, citation, raw_id):
    row = conn.execute(
        "SELECT pattern_type, description, created_at "
        "FROM flagged_patterns WHERE pattern_id = ? AND student_id = ?",
        (raw_id, student_id),
    ).fetchone()
    if row is None:
        return {"id": citation, "kind": "pattern", "text": f"Missing pattern {raw_id}", "detail": {}}

    detail = {
        "pattern_type": row["pattern_type"],
        "description": row["description"],
        "created_at": row["created_at"],
    }
    text = f"Previously flagged [{row['pattern_type']}]: {row['description']}"
    return {"id": citation, "kind": "pattern", "text": text, "detail": detail}


def _fmt_num(n) -> str:
    """Render 14.0 as '14', 14.5 as '14.5'."""
    if isinstance(n, float) and n.is_integer():
        return str(int(n))
    return str(n)


# -------- Manual test --------
if __name__ == "__main__":
    import json
    from tools.get_records import get_student_historical_records

    # Grab some real citation IDs from Amina's record
    record = get_student_historical_records("S001")
    sample_citations = []

    # First score citation
    for term, subjects in record["scores_by_term"].items():
        for subject, assignments in subjects.items():
            sample_citations.append(assignments[0]["citation_id"])
            break
        break
    # First observation citation
    if record["observations"]:
        sample_citations.append(record["observations"][0]["citation_id"])
    # Add a bogus one to prove the fallback works
    sample_citations.append("score:99999")

    print("=== Resolved citations for S001 ===")
    for item in resolve_citations("S001", sample_citations):
        print(json.dumps(item, indent=2, default=str))
