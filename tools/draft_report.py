"""
Tool 3: draft_plain_language_report

Stores a plain-language draft report for an educator/guardian, with
explicit citations. The report starts in status='draft' and cannot be
finalized without human approval via approve_report() (below).

INVARIANT: This tool only drafts. It never finalizes. The status column
starts as 'draft' and only approve_report() can move it to 'approved'.
"""

import json
from datetime import datetime, timezone
from typing import Any
from tools.db import get_connection


def draft_plain_language_report(
    student_id: str,
    summary_text: str,
    citations: list[str],
) -> dict[str, Any]:
    """
    Store a plain-language draft report with citations.

    Args:
        student_id: The student's ID (e.g., "S001").
        summary_text: Jargon-free summary text. Should reference observable
                      patterns, not fixed labels or verdicts.
        citations: A non-empty list of citation IDs supporting the summary.

    Returns:
        A dict with report_id, status='draft', or an error dict.
    """
    # --- Validation ------------------------------------------------------
    if not summary_text or not summary_text.strip():
        return {"error": "empty_summary", "message": "summary_text cannot be empty."}

    if not citations:
        return {
            "error": "no_citations",
            "message": "At least one citation is required for a report.",
        }

    conn = get_connection()
    try:
        exists = conn.execute(
            "SELECT 1 FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
        if exists is None:
            return {"error": "student_not_found", "student_id": student_id}

        bad = _verify_citations(conn, student_id, citations)
        if bad:
            return {
                "error": "invalid_citations",
                "message": "These citations do not point to real records for this student.",
                "bad_citations": bad,
            }

        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        cur = conn.execute(
            "INSERT INTO draft_reports "
            "(student_id, summary_text, citations, status, created_at) "
            "VALUES (?, ?, ?, 'draft', ?)",
            (student_id, summary_text.strip(), json.dumps(citations), created_at),
        )
        conn.commit()
        report_id = cur.lastrowid

        return {
            "status": "ok",
            "report_id": report_id,
            "student_id": student_id,
            "draft_status": "draft",
            "summary_text": summary_text.strip(),
            "citations": citations,
            "created_at": created_at,
        }
    finally:
        conn.close()


def approve_report(
    report_id: int,
    approved_by: str,
    final_text: str | None = None,
) -> dict[str, Any]:
    """
    Human-in-the-loop gate. Moves a draft report to 'approved'.
    If final_text is provided, it replaces summary_text (teacher edits).

    This is the ONLY way a report can move out of 'draft'.
    """
    if not approved_by or not approved_by.strip():
        return {"error": "missing_approver", "message": "approved_by is required."}

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT report_id, status, summary_text FROM draft_reports WHERE report_id = ?",
            (report_id,),
        ).fetchone()

        if row is None:
            return {"error": "report_not_found", "report_id": report_id}

        if row["status"] != "draft":
            return {
                "error": "not_a_draft",
                "message": f"Report is already '{row['status']}'.",
            }

        approved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        final = (final_text if final_text is not None else row["summary_text"]).strip()

        conn.execute(
            "UPDATE draft_reports "
            "SET status = 'approved', approved_at = ?, approved_by = ?, final_text = ? "
            "WHERE report_id = ?",
            (approved_at, approved_by.strip(), final, report_id),
        )
        conn.commit()

        return {
            "status": "ok",
            "report_id": report_id,
            "draft_status": "approved",
            "approved_by": approved_by.strip(),
            "approved_at": approved_at,
            "final_text": final,
        }
    finally:
        conn.close()


def _verify_citations(conn, student_id: str, citations: list[str]) -> list[str]:
    """Same logic as in flag_pattern. Kept local for module independence."""
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
        elif kind == "pattern":
            row = conn.execute(
                "SELECT 1 FROM flagged_patterns WHERE pattern_id = ? AND student_id = ?",
                (raw_id, student_id),
            ).fetchone()
        else:
            row = None
        if row is None:
            bad.append(c)
    return bad


if __name__ == "__main__":
    import json as _json

    print("--- Draft a report for S001 ---")
    draft = draft_plain_language_report(
        student_id="S001",
        summary_text=(
            "Amina has shown a steady improvement in Mathematics across the year. "
            "Her teacher notes describe growing confidence and a willingness to help "
            "classmates. Attendance has been consistent."
        ),
        citations=["score:1", "score:49", "observation:2", "observation:3"],
    )
    print(_json.dumps(draft, indent=2))

    if draft.get("status") == "ok":
        rid = draft["report_id"]

        print()
        print("--- Teacher approves with a small edit ---")
        approved = approve_report(
            report_id=rid,
            approved_by="JM",
            final_text=(
                "Amina has shown steady improvement in Mathematics across the year. "
                "Her teacher notes describe growing confidence and a willingness to help "
                "classmates. Attendance has been consistent."
            ),
        )
        print(_json.dumps(approved, indent=2))

        print()
        print("--- Try to approve the same report again ---")
        again = approve_report(report_id=rid, approved_by="JM")
        print(_json.dumps(again, indent=2))
