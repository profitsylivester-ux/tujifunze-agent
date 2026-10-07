"""
Tool 1: get_student_historical_records

Returns everything we know about a student across all terms:
  - profile (id, name, grade, cohort)
  - scores grouped by term -> subject -> list of assignments
  - attendance summary per term
  - raw teacher observations with dates and source IDs

Every record returned includes a `citation_id` so downstream nodes can
prove where a claim came from.
"""

from typing import Any
from tools.db import get_connection


def get_student_historical_records(student_id: str) -> dict[str, Any]:
    """
    Fetch a student's complete longitudinal record across all terms.

    Args:
        student_id: The student's ID (e.g., "S001").

    Returns:
        A dict with keys: profile, scores_by_term, attendance_by_term,
        observations. If the student is not found, returns
        {"error": "student_not_found", "student_id": ...}.
    """
    conn = get_connection()
    try:
        # --- Profile -----------------------------------------------------
        profile_row = conn.execute(
            "SELECT student_id, full_name, grade_level, cohort_year "
            "FROM students WHERE student_id = ?",
            (student_id,),
        ).fetchone()

        if profile_row is None:
            return {
                "error": "student_not_found",
                "student_id": student_id,
            }

        profile = {
            "student_id": profile_row["student_id"],
            "full_name": profile_row["full_name"],
            "grade_level": profile_row["grade_level"],
            "cohort_year": profile_row["cohort_year"],
        }

        # --- Scores grouped by term -> subject ---------------------------
        score_rows = conn.execute(
            "SELECT record_id, term, subject, assignment_name, "
            "       assignment_date, score, max_score "
            "FROM scores WHERE student_id = ? "
            "ORDER BY term, subject, assignment_date",
            (student_id,),
        ).fetchall()

        scores_by_term: dict[str, dict[str, list[dict[str, Any]]]] = {}
        for r in score_rows:
            term = r["term"]
            subject = r["subject"]
            scores_by_term.setdefault(term, {}).setdefault(subject, []).append({
                "citation_id": f"score:{r['record_id']}",
                "assignment_name": r["assignment_name"],
                "assignment_date": r["assignment_date"],
                "score": r["score"],
                "max_score": r["max_score"],
                "percent": round(100.0 * r["score"] / r["max_score"], 1),
            })

        # --- Attendance summary per term ---------------------------------
        att_rows = conn.execute(
            "SELECT term, status, COUNT(*) AS n "
            "FROM attendance WHERE student_id = ? "
            "GROUP BY term, status ORDER BY term, status",
            (student_id,),
        ).fetchall()

        attendance_by_term: dict[str, dict[str, int]] = {}
        for r in att_rows:
            attendance_by_term.setdefault(r["term"], {})[r["status"]] = r["n"]

        # Add a present-rate per term for convenience
        for term, counts in attendance_by_term.items():
            total = sum(counts.values())
            present = counts.get("present", 0)
            counts["total_days"] = total
            counts["present_rate"] = round(100.0 * present / total, 1) if total else 0.0

        # --- Qualitative teacher observations ----------------------------
        obs_rows = conn.execute(
            "SELECT record_id, term, observation_date, teacher_initials, note "
            "FROM observations WHERE student_id = ? "
            "ORDER BY observation_date",
            (student_id,),
        ).fetchall()

        observations = [
            {
                "citation_id": f"observation:{r['record_id']}",
                "term": r["term"],
                "date": r["observation_date"],
                "teacher_initials": r["teacher_initials"],
                "note": r["note"],
            }
            for r in obs_rows
        ]

        return {
            "profile": profile,
            "scores_by_term": scores_by_term,
            "attendance_by_term": attendance_by_term,
            "observations": observations,
        }
    finally:
        conn.close()


if __name__ == "__main__":
    # Quick manual test when run directly:
    #   python -m tools.get_records
    import json
    result = get_student_historical_records("S001")
    print(json.dumps(result, indent=2, default=str))
