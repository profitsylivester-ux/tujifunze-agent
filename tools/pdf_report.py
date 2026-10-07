"""
PDF report generator for the Tujifunze Agent.

Produces a professional A4 PDF report with:
  - School header
  - Student metadata block
  - Report metadata block (teacher, class, term, year, guardian)
  - Plain-language summary
  - Verified patterns with human-readable citations
  - Full citation appendix
  - Teacher remarks section
  - Footer with ethical disclaimer

Usage:
    generate_pdf_report(
        student_profile={...},
        summary_text="...",
        verified_patterns=[...],
        citations=[...],
        meta={...},
    ) -> bytes   # PDF bytes, ready for st.download_button
"""

from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)

from tools.citation_resolver import resolve_citations


# ----- Brand palette -----
BRAND_TEAL = colors.HexColor("#0d7377")
BRAND_TEAL_LIGHT = colors.HexColor("#e6f4f5")
BRAND_TEXT = colors.HexColor("#0f2027")
BRAND_MUTED = colors.HexColor("#5a6b73")
BRAND_BORDER = colors.HexColor("#d6e2e5")

PATTERN_COLORS = {
    "strength": colors.HexColor("#15803d"),
    "emerging": colors.HexColor("#2563eb"),
    "struggle": colors.HexColor("#b45309"),
    "attendance_concern": colors.HexColor("#b91c1c"),
}

PATTERN_LABELS = {
    "strength": "Strength",
    "emerging": "Emerging",
    "struggle": "Struggle",
    "attendance_concern": "Attendance Concern",
}


def _styles():
    base = getSampleStyleSheet()
    return {
        "school": ParagraphStyle(
            "school",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=BRAND_TEAL,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        "title": ParagraphStyle(
            "title",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=14,
            textColor=BRAND_MUTED,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=BRAND_TEAL,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=BRAND_TEXT,
            alignment=TA_JUSTIFY,
        ),
        "summary": ParagraphStyle(
            "summary",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            textColor=BRAND_TEXT,
            alignment=TA_JUSTIFY,
            spaceAfter=4,
        ),
        "meta_label": ParagraphStyle(
            "meta_label",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=BRAND_MUTED,
        ),
        "meta_value": ParagraphStyle(
            "meta_value",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=BRAND_TEXT,
        ),
        "pattern_label": ParagraphStyle(
            "pattern_label",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            spaceAfter=3,
        ),
        "pattern_desc": ParagraphStyle(
            "pattern_desc",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=BRAND_TEXT,
            spaceAfter=4,
        ),
        "cite": ParagraphStyle(
            "cite",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=BRAND_MUTED,
            leftIndent=10,
            bulletIndent=2,
            spaceAfter=1,
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=11,
            textColor=BRAND_MUTED,
            alignment=TA_CENTER,
        ),
    }


def generate_pdf_report(
    student_profile: dict,
    summary_text: str,
    verified_patterns: list,
    citations: list,
    meta: dict,
) -> bytes:
    """
    Build the PDF and return it as bytes.

    meta keys (all optional, sensible defaults provided):
        school_name, class_section, academic_year, term,
        teacher_name, guardian_name, teacher_remarks, report_id
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Tujifunze Report - {student_profile.get('full_name', '')}",
        author=meta.get("teacher_name", ""),
    )

    S = _styles()
    story = []

    # -------- Header --------
    story.append(Paragraph(meta.get("school_name") or "Tujifunze Academy", S["school"]))
    story.append(Paragraph("Longitudinal Learning Report", S["title"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BRAND_TEAL, spaceAfter=12))

    # -------- Two-column metadata table --------
    story.append(_metadata_table(student_profile, meta, S))
    story.append(Spacer(1, 8))

    # -------- Summary --------
    story.append(Paragraph("SUMMARY", S["h2"]))
    story.append(Paragraph(summary_text or "(no summary)", S["summary"]))

    # -------- Verified patterns + resolved citations --------
    if verified_patterns:
        story.append(Paragraph("VERIFIED PATTERNS", S["h2"]))
        resolved_cache = _resolve_all_citations(student_profile["student_id"], citations)
        for p in verified_patterns:
            story.append(_pattern_block(p, resolved_cache, S))

    # -------- Teacher remarks --------
    if meta.get("teacher_remarks"):
        story.append(Paragraph("TEACHER REMARKS", S["h2"]))
        story.append(Paragraph(meta["teacher_remarks"], S["summary"]))

    # -------- Footer --------
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.7, color=BRAND_BORDER, spaceAfter=8))
    footer_lines = [
        f"Report ID #{meta.get('report_id', '-')} &nbsp;|&nbsp; "
        f"Approved by {meta.get('teacher_name', 'the teacher')} on "
        f"{datetime.now().strftime('%Y-%m-%d')}",
        "This report contains sourced observations only. "
        "It does not assign labels, tracks, or verdicts.",
        "Tujifunze Agent - automatically generated, teacher verified.",
    ]
    for line in footer_lines:
        story.append(Paragraph(line, S["footer"]))

    doc.build(story)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _metadata_table(student_profile: dict, meta: dict, S: dict) -> Table:
    """Render a two-column metadata block."""
    left_rows = [
        ["Student", student_profile.get("full_name", "")],
        ["Student ID", student_profile.get("student_id", "")],
        ["Grade", str(student_profile.get("grade_level", ""))],
        ["Cohort", str(student_profile.get("cohort_year", ""))],
    ]
    right_rows = [
        ["Teacher", meta.get("teacher_name", "")],
        ["Class / Section", meta.get("class_section", "")],
        ["Academic Year", meta.get("academic_year", "")],
        ["Term", meta.get("term", "")],
    ]
    if meta.get("guardian_name"):
        right_rows.append(["Guardian", meta["guardian_name"]])

    data = []
    for i in range(max(len(left_rows), len(right_rows))):
        left = left_rows[i] if i < len(left_rows) else ["", ""]
        right = right_rows[i] if i < len(right_rows) else ["", ""]
        data.append([
            Paragraph(left[0], S["meta_label"]),
            Paragraph(left[1], S["meta_value"]),
            Paragraph(right[0], S["meta_label"]),
            Paragraph(right[1], S["meta_value"]),
        ])

    table = Table(data, colWidths=[28 * mm, 55 * mm, 33 * mm, 55 * mm])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, BRAND_BORDER),
    ]))
    return table


def _resolve_all_citations(student_id: str, citations: list) -> dict:
    """Resolve every citation once, return a dict keyed by citation id."""
    resolved = resolve_citations(student_id, citations)
    return {r["id"]: r["text"] for r in resolved}


def _pattern_block(pattern: dict, resolved_cache: dict, S: dict):
    """Return a list of flowables for a single pattern (label + desc + cites)."""
    ptype = pattern.get("pattern_type", "unknown")
    label_color = PATTERN_COLORS.get(ptype, BRAND_MUTED)
    label_text = PATTERN_LABELS.get(ptype, ptype.replace("_", " ").title())

    label_style = ParagraphStyle(
        f"lbl_{ptype}",
        parent=S["pattern_label"],
        textColor=label_color,
    )

    flowables = [
        Paragraph(f"[{label_text.upper()}]", label_style),
        Paragraph(pattern.get("description", ""), S["pattern_desc"]),
    ]

    cites = pattern.get("source_citations", [])
    if cites:
        for cid in cites:
            text = resolved_cache.get(cid, cid)
            flowables.append(Paragraph(f"- {_escape(text)}", S["cite"]))

    flowables.append(Spacer(1, 6))
    return KeepTogether(flowables)


def _escape(text: str) -> str:
    """Escape characters that ReportLab's mini-HTML treats specially."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# -------- Manual test --------
if __name__ == "__main__":
    from pathlib import Path

    # Realistic sample data
    profile = {
        "student_id": "S001",
        "full_name": "Amina Hassan",
        "grade_level": 7,
        "cohort_year": 2024,
    }
    summary = (
        "Amina has shown steady improvement in Mathematics across the year. "
        "Her teacher notes describe growing confidence and a willingness to help "
        "classmates. Attendance has been consistent."
    )
    patterns = [
        {
            "pattern_type": "strength",
            "description": "Math scores rose consistently from 70% to 90% across Terms 1-3.",
            "source_citations": ["score:1", "score:49"],
        },
        {
            "pattern_type": "emerging",
            "description": "Increasing confidence in group work and class participation.",
            "source_citations": ["observation:2", "observation:3"],
        },
    ]
    citations = ["score:1", "score:49", "observation:2", "observation:3"]
    meta = {
        "school_name": "Tujifunze Academy",
        "class_section": "Grade 7A",
        "academic_year": "2024",
        "term": "Term 3 2024",
        "teacher_name": "Mr. Faida Sylivester",
        "guardian_name": "Mrs. Hassan",
        "teacher_remarks": (
            "Amina has had a strong year. I recommend continuing to challenge her "
            "with extension problems in Mathematics next term."
        ),
        "report_id": 42,
    }

    pdf_bytes = generate_pdf_report(profile, summary, patterns, citations, meta)
    out = Path("test_report.pdf")
    out.write_bytes(pdf_bytes)
    print(f"PDF written: {out} ({len(pdf_bytes)} bytes)")
    print("Open it to inspect the layout.")
