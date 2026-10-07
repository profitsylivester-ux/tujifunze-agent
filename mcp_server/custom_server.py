"""
Tujifunze MCP Server (stdio transport)

Exposes 3 tools over the Model Context Protocol:
  1. get_student_historical_records(student_id)
  2. flag_learning_pattern(student_id, pattern_type, description, source_citations)
  3. draft_plain_language_report(student_id, summary_text, citations)

Plus a bonus read-only tool:
  4. list_students()

Run standalone for testing:
    python -m mcp_server.custom_server

Or let an MCP client (e.g., the LangGraph agent) spawn it as a subprocess.
"""

from typing import Any

from mcp.server.fastmcp import FastMCP

from tools.get_records import get_student_historical_records as _get_records
from tools.flag_pattern import flag_learning_pattern as _flag_pattern
from tools.draft_report import draft_plain_language_report as _draft_report
from tools.db import get_connection


# Name shown to MCP clients
mcp = FastMCP("tujifunze-agent")


@mcp.tool()
def get_student_historical_records(student_id: str) -> dict[str, Any]:
    """
    Fetch a student's full longitudinal record across all terms:
    profile, scores by term/subject, attendance summary, teacher observations.

    Every returned record includes a citation_id (e.g. "score:14",
    "observation:2") that can be used in downstream tools.

    Args:
        student_id: The student's ID, e.g. "S001".
    """
    return _get_records(student_id)


@mcp.tool()
def flag_learning_pattern(
    student_id: str,
    pattern_type: str,
    description: str,
    source_citations: list[str],
) -> dict[str, Any]:
    """
    Record a verified learning pattern (strength / struggle / emerging /
    attendance_concern) against a student, with citations proving it.

    INVARIANT: Only sourced, observable patterns can be recorded.
    No fixed labels, tracks, or verdicts.

    Args:
        student_id: e.g. "S001".
        pattern_type: One of "strength", "struggle", "emerging", "attendance_concern".
        description: A plain observational sentence. No career/track labels.
        source_citations: Non-empty list of citation IDs, e.g. ["score:14", "observation:2"].
    """
    return _flag_pattern(student_id, pattern_type, description, source_citations)


@mcp.tool()
def draft_plain_language_report(
    student_id: str,
    summary_text: str,
    citations: list[str],
) -> dict[str, Any]:
    """
    Store a plain-language draft report for an educator/guardian.
    Draft starts in status='draft' and requires human approval to finalize.

    Args:
        student_id: e.g. "S001".
        summary_text: Jargon-free, observational summary.
        citations: Non-empty list of citation IDs supporting the summary.
    """
    return _draft_report(student_id, summary_text, citations)


@mcp.tool()
def list_students() -> list[dict[str, Any]]:
    """
    Return a lightweight roster of all students in the database.
    Useful for the UI to populate a dropdown.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT student_id, full_name, grade_level, cohort_year "
            "FROM students ORDER BY student_id"
        ).fetchall()
        return [
            {
                "student_id": r["student_id"],
                "full_name": r["full_name"],
                "grade_level": r["grade_level"],
                "cohort_year": r["cohort_year"],
            }
            for r in rows
        ]
    finally:
        conn.close()


if __name__ == "__main__":
    # Runs the server over stdio. An MCP client connects to stdin/stdout.
    mcp.run()
