"""
Tool 2: flag_learning_pattern

Writes a verified pattern (strength or struggle) to a student's profile,
with explicit citations back to the source records that support it.

INVARIANT: This tool only records *sourced* patterns. It never assigns
a fixed track, career label, or verdict to a child. The description must
be observational and cite at least one source.
"""

import json
from datetime import datetime, timezone
from typing import Any
from tools.db import get_connection


VALID_PATTERN_TYPES = {"strength", "struggle", "emerging", "attendance_concern"}


def flag_learning_pattern(
    student_id: str,
    pattern_type: str,
    description: str,
    source_citations: list[str],
) -> dict[str, Any]:
    """
    Persist a verified learning pattern to the student's profile.

    Args:
        student_id: The student's ID (e.g., "S001").
        pattern_type: One of "strength", "struggle", "emerging", "attendance_concern".
        description: A plain observational description. Must NOT contain labels
                     or verdicts like "will be an engineer" or "is weak at math".
        source_citations: A non-empty list of citation IDs (e.g., ["score:14",
                          "observation:2"]) proving the pattern.

    Returns:
        A dict with pattern_id, created_at, and the stored record,
        or an error dict if validation fails.
    """
    # --- Validation ------------------------------------------------------
    if pattern_type not in VALID_PATTERN_TYPES:
        return {
            "error": "invalid_pattern_type",
            "message": f"pattern_type must be one of {sorted(VALID_PATTERN_TYPES)}",
            "got": pattern_type,
        }

    if not description or not description.strip():
        return {
            "error": "empty_description",
            "message": "description cannot be empty",
        }

    if not source_citations:
        return {
            "error": "no_citations",
            "message": "At least one source citation is required to flag a pattern.",
        }

    # --- Confirm student exists -----------------------------------------
    conn = get_connection()
    try:
        exists = conn.execute(
            "SELECT 1 FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
        if exists is None:
            return {"error": "student_not_found", "student_id": student_id}

        # --- Verify every citation actually exists in the DB -------------
        bad_citations = _verify_citations(conn, student_id, source_citations)
        if bad_citations:
            return {
                "error": "invalid_citations",
                "message": "These citations do not point to real records for this student.",
                "bad_citations": bad_citations,
            }

        # --- Insert ------------------------------------------------------
        citations_json = json.dumps(source_citations)
        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

        cur = conn.execute(
            "INSERT INTO flagged_patterns "
            "(student_id, pattern_type, description, source_citations, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (student_id, pattern_type, description.strip(), citations_json, created_at),
        )
        conn.commit()
        pattern_id = cur.lastrowid

        return {
            "status": "ok",
            "pattern_id": pattern_id,
            "student_id": student_id,
            "pattern_type": pattern_type,
            "description": description.strip(),
            "source_citations": source_citations,
            "created_at": created_at,
        }
    finally:
        conn.close()


def _verify_citations(
    conn, student_id: str, citations: list[str]
) -> list[str]:
    """
    Return the subset of `citations` that do NOT resolve to a real record
    belonging to this student. Empty list = all valid.
    """
    bad: list[str] = []
    for c in citations:
        if not isinstance(c, str) or ":" not in c:
            bad.append(c)
            continue

        kind, _, raw_id = c.partition(":")
        if kind == "score":
            row = conn.execute(
                "SELECT 1 FROM scores WHERE record_id = ? AND student_id = ?",
                (raw_id, student_id),
            ).fetchone()
        elif kind == "observation":
            row = conn.execute(
                "SELECT 1 FROM observations WHERE record_id = ? AND student_id = ?",
                (raw_id, student_id),
            ).fetchone()
        elif kind == "attendance":
            row = conn.execute(
                "SELECT 1 FROM attendance WHERE record_id = ? AND student_id = ?",
                (raw_id, student_id),
            ).fetchone()
        else:
            row = None

        if row is None:
            bad.append(c)

    return bad


if __name__ == "__main__":
    # Quick manual test — writes one pattern for S001, then reads it back.
    import json as _json

    print("--- Valid pattern ---")
    result = flag_learning_pattern(
        student_id="S001",
        pattern_type="strength",
        description=(
            "Consistent improvement in Math across all three terms, "
            "moving from 70% on the Term 1 Fractions Quiz to 90% on the "
            "Term 3 Geometry Quiz."
        ),
        source_citations=["score:1", "score:49"],
    )
    print(_json.dumps(result, indent=2))

    print()
    print("--- Invalid: fake citation ---")
    result = flag_learning_pattern(
        student_id="S001",
        pattern_type="strength",
        description="Testing rejection of fake citations.",
        source_citations=["score:99999"],
    )
    print(_json.dumps(result, indent=2))

    print()
    print("--- Invalid: no citations ---")
    result = flag_learning_pattern(
        student_id="S001",
        pattern_type="strength",
        description="Testing rejection of empty citations.",
        source_citations=[],
    )
    print(_json.dumps(result, indent=2))
