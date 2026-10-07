"""
Tujifunze Agent - Teacher Dashboard (Streamlit)

Complete single-file UI:
  1. Page config + CSS
  2. Login gate
  3. Sidebar with student selector + logout
  4. Main dashboard
  5. Agent runner (streams nodes as pills)
  6. Human-in-the-loop gate (editable draft + Approve / Reject)
  7. Download approved report
"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

import hmac
import sys
from datetime import datetime
import base64
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from langgraph.types import Command

from agent.graph import graph as agent_graph
from agent.llm import describe_backend
from tools.db import get_connection
from tools.pdf_report import generate_pdf_report


# =============================================================================
# 1. Page config
# =============================================================================
st.set_page_config(
    page_title="Tujifunze Agent",
    page_icon=":mortar_board:",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# 2. CSS
# =============================================================================
st.markdown(
    """
    <style>
        :root {
            --tj-primary: #0d7377;
            --tj-primary-dark: #0a5c5f;
            --tj-primary-light: #14a5a9;
            --tj-success: #15803d;
            --tj-warning: #b45309;
            --tj-danger: #b91c1c;
            --tj-text: #0f2027;
            --tj-text-muted: #5a6b73;
            --tj-border: #d6e2e5;
        }
        .stApp {
            background-color: #f4f8f9;
            background-image:
                radial-gradient(circle at 1px 1px, rgba(13, 115, 119, 0.06) 1px, transparent 0);
            background-size: 24px 24px;
        }
        html, body, [class*="css"] {
            color: #0f2027;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                         "Helvetica Neue", sans-serif;
        }
        #MainMenu, footer {visibility: hidden;}
        h1 { color: #0f2027 !important; font-weight: 800 !important; letter-spacing: -0.6px !important; }
        h2 { color: #0f2027 !important; font-weight: 700 !important; }
        h3 { color: #0f2027 !important; font-weight: 600 !important; }
        .stCaption, [data-testid="stCaptionContainer"] { color: #5a6b73 !important; }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0d7377 0%, #0a5c5f 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 { color: #ffffff !important; }
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stCaption { color: #c8e6e7 !important; }
        section[data-testid="stSidebar"] hr {
            border-color: rgba(255, 255, 255, 0.18) !important;
            margin: 1.1rem 0 !important;
        }
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background: rgba(255, 255, 255, 0.14) !important;
            border: 1px solid rgba(255, 255, 255, 0.28) !important;
        }
        section[data-testid="stSidebar"] div[data-baseweb="select"] span { color: #ffffff !important; }
        section[data-testid="stSidebar"] div[data-baseweb="select"] svg { fill: #ffffff !important; }
        section[data-testid="stSidebar"] [data-testid="stJson"] {
            background: rgba(255, 255, 255, 0.10);
            border-radius: 10px;
            padding: 0.5rem 0.7rem;
        }
        section[data-testid="stSidebar"] [data-testid="stJson"] * { color: #eaf5f5 !important; }
        section[data-testid="stSidebar"] .stButton > button {
            background: rgba(255, 255, 255, 0.14) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.30) !important;
        }
        section[data-testid="stSidebar"] .stButton > button:hover {
            background: rgba(255, 255, 255, 0.24) !important;
        }

        div[data-baseweb="popover"] div[role="listbox"],
        div[data-baseweb="popover"] ul {
            background: #ffffff !important;
            border: 1px solid #d6e2e5 !important;
            border-radius: 10px !important;
            box-shadow: 0 8px 24px rgba(15, 32, 39, 0.15) !important;
            padding: 0.35rem !important;
        }
        div[data-baseweb="popover"] li,
        div[data-baseweb="popover"] div[role="option"] {
            color: #0f2027 !important;
            background: #ffffff !important;
            font-weight: 600 !important;
            border-radius: 6px !important;
            padding: 0.5rem 0.8rem !important;
        }
        div[data-baseweb="popover"] li:hover,
        div[data-baseweb="popover"] div[role="option"]:hover,
        div[data-baseweb="popover"] li[aria-selected="true"],
        div[data-baseweb="popover"] div[role="option"][aria-selected="true"] {
            background: #e6f4f5 !important;
            color: #0a5c5f !important;
        }
        div[data-baseweb="popover"] li *,
        div[data-baseweb="popover"] div[role="option"] * {
            color: #0f2027 !important;
            font-weight: 600 !important;
        }

        .stButton > button {
            border-radius: 10px;
            font-weight: 700;
            padding: 0.6rem 1.3rem;
            transition: all 0.18s ease;
            border: none;
            font-size: 0.95rem;
        }
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #0d7377 0%, #14a5a9 100%);
            color: #ffffff !important;
            box-shadow: 0 2px 8px rgba(13, 115, 119, 0.28);
        }
        .stButton > button[kind="primary"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 20px rgba(13, 115, 119, 0.38);
        }
        .stButton > button[kind="secondary"] {
            background: #ffffff !important;
            color: #0d7377 !important;
            border: 1.5px solid #0d7377 !important;
        }
        .stButton > button[kind="secondary"]:hover {
            background: #0d7377 !important;
            color: #ffffff !important;
        }

        div[data-testid="stAlert"] {
            border-radius: 10px !important;
            padding: 0.9rem 1.1rem !important;
        }
        div[data-testid="stAlert"] p,
        div[data-testid="stAlert"] span {
            color: #0f2027 !important;
            font-weight: 500 !important;
        }

        .stTextArea textarea {
            border-radius: 10px !important;
            border: 1.5px solid #d6e2e5 !important;
            font-size: 1rem !important;
            line-height: 1.6 !important;
            color: #0f2027 !important;
            background: #ffffff !important;
        }
        .stTextArea textarea:focus {
            border-color: #0d7377 !important;
            box-shadow: 0 0 0 3px rgba(13, 115, 119, 0.12) !important;
        }

        .tj-banner {
            background: linear-gradient(135deg, #e6f4f5 0%, #d4ebed 100%);
            border-left: 4px solid #0d7377;
            border-radius: 10px;
            padding: 1rem 1.3rem;
            margin-bottom: 1.4rem;
            color: #0f2027;
            font-size: 0.98rem;
            line-height: 1.5;
            font-weight: 500;
            box-shadow: 0 1px 3px rgba(13, 115, 119, 0.06);
        }
        .tj-student-card {
            background: #ffffff;
            border-left: 5px solid #0d7377;
            border-radius: 12px;
            padding: 1.1rem 1.5rem;
            margin-bottom: 1.4rem;
            box-shadow: 0 2px 10px rgba(15, 32, 39, 0.05);
        }
        .tj-student-name {
            font-size: 1.4rem;
            font-weight: 800;
            color: #0f2027;
            margin: 0;
            letter-spacing: -0.3px;
        }
        .tj-student-meta {
            color: #5a6b73;
            font-size: 0.92rem;
            margin-top: 0.25rem;
        }

        .tj-node {
            display: inline-block;
            padding: 0.4rem 0.9rem;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 700;
            margin-right: 0.5rem;
            margin-bottom: 0.4rem;
            background: #eef2f4;
            color: #5a6b73;
            border: 1.5px solid #d6e2e5;
        }
        .tj-node-done   { background: #dcfce7; color: #166534; border-color: #86efac; }
        .tj-node-active { background: #fef3c7; color: #92400e; border-color: #fcd34d; }
        .tj-node-paused { background: #dbeafe; color: #1e40af; border-color: #93c5fd; }

        .tj-pattern {
            padding: 1rem 1.1rem;
            border-radius: 10px;
            margin-bottom: 0.7rem;
            border-left: 4px solid #d6e2e5;
            background: #ffffff;
            box-shadow: 0 1px 3px rgba(15, 32, 39, 0.04);
        }
        .tj-pattern-strength           { border-left-color: #15803d; background: #f0fdf4; }
        .tj-pattern-emerging           { border-left-color: #2563eb; background: #eff6ff; }
        .tj-pattern-struggle           { border-left-color: #b45309; background: #fffbeb; }
        .tj-pattern-attendance_concern { border-left-color: #b91c1c; background: #fef2f2; }
        .tj-pattern-type {
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            font-weight: 800;
            margin-bottom: 0.3rem;
        }
        .tj-pattern-strength           .tj-pattern-type { color: #15803d; }
        .tj-pattern-emerging           .tj-pattern-type { color: #2563eb; }
        .tj-pattern-struggle           .tj-pattern-type { color: #b45309; }
        .tj-pattern-attendance_concern .tj-pattern-type { color: #b91c1c; }
        .tj-pattern-desc {
            color: #0f2027;
            font-size: 0.96rem;
            line-height: 1.55;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }

        .tj-chip {
            display: inline-block;
            background: #e6f4f5;
            color: #0a5c5f;
            border: 1px solid #b8dadc;
            border-radius: 999px;
            padding: 0.18rem 0.7rem;
            font-size: 0.72rem;
            font-family: 'SF Mono', Menlo, Consolas, monospace;
            margin: 0 0.3rem 0.3rem 0;
            font-weight: 700;
        }

        .tj-section-title {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 1.3px;
            color: #5a6b73;
            font-weight: 800;
            margin: 1.6rem 0 0.7rem 0;
        }

        .tj-login-title {
            text-align: center;
            font-size: 2.2rem;
            font-weight: 800;
            color: #0f2027;
            margin-bottom: 0.5rem;
            letter-spacing: -0.6px;
        }
        .tj-login-sub {
            text-align: center;
            color: #5a6b73;
            font-size: 1rem;
            margin-bottom: 2rem;
        }
        .tj-login-hint {
            text-align: center;
            font-size: 0.78rem;
            color: #8a9ba1;
            margin-top: 1.2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# 3. Login gate
# =============================================================================
def _get_auth_credentials() -> dict:
    try:
        users = st.secrets["auth"]["users"]
        return {"users": {u["username"]: {"password": u["password"]} for u in users}}
    except Exception:
        return {"users": {"teacher": {"password": "tujifunze2024"}}}


def _check_login() -> bool:
    return bool(st.session_state.get("authenticated", False))


def _render_login_screen() -> None:
    st.markdown(
        "<style>section[data-testid='stSidebar'] {display: none;} "
        ".block-container {padding-top: 5rem; max-width: 460px;}</style>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='tj-login-title'>Tujifunze Agent</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='tj-login-sub'>Educator access - sign in to view student records</div>",
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="e.g. teacher")
        password = st.text_input("Password", type="password", placeholder="********")
        submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

    if submitted:
        creds = _get_auth_credentials()
        user_record = creds["users"].get(username.strip())
        if user_record and hmac.compare_digest(user_record["password"], password):
            st.session_state["authenticated"] = True
            st.session_state["username"] = username.strip()
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.markdown(
        "<div class='tj-login-hint'>Access is restricted to verified educators. "
        "Student records are confidential.</div>",
        unsafe_allow_html=True,
    )


if not _check_login():
    _render_login_screen()
    st.stop()


# =============================================================================
# 4. Data helpers
# =============================================================================
def _resolve_preview(citation_id: str) -> str:
    """Turn score:1 into a readable short label for the chips in the UI."""
    conn = get_connection()
    try:
        if not isinstance(citation_id, str) or ":" not in citation_id:
            return citation_id
        kind, _, raw_id = citation_id.partition(":")
        if kind == "score":
            row = conn.execute(
                "SELECT assignment_name, assignment_date FROM scores WHERE record_id = ?",
                (raw_id,),
            ).fetchone()
            if row:
                return f"{row['assignment_name']} - {row['assignment_date']}"
        elif kind == "observation":
            row = conn.execute(
                "SELECT observation_date, teacher_initials FROM observations WHERE record_id = ?",
                (raw_id,),
            ).fetchone()
            if row:
                return f"Note {row['observation_date']} ({row['teacher_initials']})"
        elif kind == "attendance":
            row = conn.execute(
                "SELECT school_day, status FROM attendance WHERE record_id = ?",
                (raw_id,),
            ).fetchone()
            if row:
                return f"{row['school_day']} - {row['status']}"
        elif kind == "pattern":
            row = conn.execute(
                "SELECT pattern_type FROM flagged_patterns WHERE pattern_id = ?",
                (raw_id,),
            ).fetchone()
            if row:
                return f"Pattern: {row['pattern_type']}"
        return citation_id
    finally:
        conn.close()


def _resolve_preview(citation_id: str) -> str:
    """Turn score:1 into a readable short label for the chips in the UI."""
    conn = get_connection()
    try:
        if not isinstance(citation_id, str) or ":" not in citation_id:
            return citation_id
        kind, _, raw_id = citation_id.partition(":")
        if kind == "score":
            row = conn.execute(
                "SELECT assignment_name, assignment_date FROM scores WHERE record_id = ?",
                (raw_id,),
            ).fetchone()
            if row:
                return f"{row['assignment_name']} - {row['assignment_date']}"
        elif kind == "observation":
            row = conn.execute(
                "SELECT observation_date, teacher_initials FROM observations WHERE record_id = ?",
                (raw_id,),
            ).fetchone()
            if row:
                return f"Note {row['observation_date']} ({row['teacher_initials']})"
        elif kind == "attendance":
            row = conn.execute(
                "SELECT school_day, status FROM attendance WHERE record_id = ?",
                (raw_id,),
            ).fetchone()
            if row:
                return f"{row['school_day']} - {row['status']}"
        elif kind == "pattern":
            row = conn.execute(
                "SELECT pattern_type FROM flagged_patterns WHERE pattern_id = ?",
                (raw_id,),
            ).fetchone()
            if row:
                return f"Pattern: {row['pattern_type']}"
        return citation_id
    finally:
        conn.close()


def _latest_term_for_student(student_id: str) -> str:
    """Return the latest term label for a student, formatted as 'Term N YYYY'."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT term FROM scores WHERE student_id = ? ORDER BY term DESC LIMIT 1",
            (student_id,),
        ).fetchone()
        if not row:
            return ""
        t = row["term"]
        if "-T" in t:
            year, _, term_num = t.partition("-T")
            return f"Term {term_num} {year}"
        return t
    finally:
        conn.close()


@st.cache_data(ttl=60)
def load_students() -> list:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT student_id, full_name, grade_level, cohort_year "
            "FROM students ORDER BY student_id"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# =============================================================================
# 5. Sidebar
# =============================================================================
with st.sidebar:
    st.markdown("## Tujifunze Agent")
    st.caption("Longitudinal Learning Insights")

    students = load_students()
    options = {f"{s['full_name']} ({s['student_id']})": s for s in students}
    selected_label = st.selectbox("Select student", list(options.keys()))
    selected = options[selected_label]

    st.divider()
    st.caption("**Active model**")
    st.json(describe_backend())

    st.divider()
    st.caption(f"Signed in as **{st.session_state.get('username', '?')}**")
    if st.button("Log out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.divider()
    st.caption("**About**")
    st.caption(
        "This agent reads a student's multi-term record and surfaces "
        "sourced, defensible patterns - never fixed labels."
    )


# =============================================================================
# 6. Main dashboard
# =============================================================================
st.markdown("# Longitudinal Learning Report")
st.markdown(
    "<div class='tj-banner'>"
    "Select a student, run the agent, review the draft, and approve to finalize. "
    "Every claim in the report is cited back to a real record."
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class='tj-student-card'>
        <div class='tj-student-name'>{selected['full_name']}</div>
        <div class='tj-student-meta'>
            Student ID {selected['student_id']} &nbsp;|&nbsp;
            Grade {selected['grade_level']} &nbsp;|&nbsp;
            Cohort {selected['cohort_year']}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# 7. Agent runner + HITL gate
# =============================================================================
NODE_ORDER = ["retrieve", "analyze", "verify", "report", "hitl"]
NODE_LABELS = {
    "retrieve": "Retrieve records",
    "analyze":  "Analyze trends",
    "verify":   "Verify citations",
    "report":   "Draft report",
    "hitl":     "Awaiting review",
}


def _render_node_pills(done: list, paused: bool = False, active: str = "") -> None:
    """Render a row of pill indicators for the agent's progress."""
    pills = []
    for n in NODE_ORDER:
        label = NODE_LABELS[n]
        if n == active:
            cls = "tj-node tj-node-active"
        elif n in done and not (paused and n == "hitl"):
            cls = "tj-node tj-node-done"
        elif paused and n == "hitl":
            cls = "tj-node tj-node-paused"
        else:
            cls = "tj-node"
        pills.append(f"<span class='{cls}'>{label}</span>")
    st.markdown("".join(pills), unsafe_allow_html=True)


def _render_patterns(patterns: list) -> None:
    for p in patterns:
        ptype = p.get("pattern_type", "unknown")
        desc = p.get("description", "")
        cites = p.get("source_citations", [])
        chips = "".join(f"<span class='tj-chip'>{_resolve_preview(c)}</span>" for c in cites)
        st.markdown(
            f"""
            <div class='tj-pattern tj-pattern-{ptype}'>
                <div class='tj-pattern-type'>{ptype.replace('_', ' ')}</div>
                <div class='tj-pattern-desc'>{desc}</div>
                <div>{chips}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _run_agent(student_id: str) -> None:
    thread_id = f"ui-{student_id}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    config = {"configurable": {"thread_id": thread_id}}

    st.session_state["interrupt_payload"] = None
    st.session_state["final_state"] = None
    st.session_state["completed_nodes"] = []
    st.session_state["thread_config"] = config
    st.session_state["edited_text"] = None

    # A single placeholder that updates live as nodes complete.
    pills_placeholder = st.empty()
    completed = []

    # Show the very first node as "active" before we start
    with pills_placeholder.container():
        _render_node_pills(completed, active="retrieve")

    for chunk in agent_graph.stream(
        {"student_id": student_id, "errors": []},
        config=config,
        stream_mode="updates",
    ):
        if "__interrupt__" in chunk:
            interrupts = chunk["__interrupt__"]
            st.session_state["interrupt_payload"] = interrupts[0].value
            completed.append("hitl")
            st.session_state["completed_nodes"] = completed
            with pills_placeholder.container():
                _render_node_pills(completed, paused=True)
            break

        for node_name, _ in chunk.items():
            completed.append(node_name)
            st.session_state["completed_nodes"] = completed
            # Mark the next node as active (if there is one)
            idx = NODE_ORDER.index(node_name) if node_name in NODE_ORDER else -1
            next_active = NODE_ORDER[idx + 1] if 0 <= idx < len(NODE_ORDER) - 1 else ""
            with pills_placeholder.container():
                _render_node_pills(completed, active=next_active)


def _approve_and_finalize(edited_text: str) -> None:
    payload = st.session_state.get("interrupt_payload")
    config = st.session_state.get("thread_config")
    if not payload or not config:
        st.error("No pending draft to approve.")
        return

    decision = {
        "approved": True,
        "approved_by": st.session_state.get("username", "unknown"),
        "final_text": edited_text,
    }

    final_state = None
    for chunk in agent_graph.stream(
        Command(resume=decision), config=config, stream_mode="updates"
    ):
        for _, update in chunk.items():
            if isinstance(update, dict):
                final_state = {**(final_state or {}), **update}

    st.session_state["final_state"] = final_state or {}
    st.session_state["interrupt_payload"] = None
    st.session_state["edited_text"] = edited_text
    st.rerun()


def _reject_draft() -> None:
    payload = st.session_state.get("interrupt_payload")
    config = st.session_state.get("thread_config")
    if payload and config:
        agent_graph.stream(
            Command(resume={"approved": False}),
            config=config,
            stream_mode="updates",
        )
    st.session_state["interrupt_payload"] = None
    st.session_state["edited_text"] = None
    st.rerun()


col_run, col_rest = st.columns([1, 4])
with col_run:
    run_clicked = st.button("Run Agent Analysis", type="primary", use_container_width=True)

if run_clicked:
    _run_agent(selected["student_id"])


payload = st.session_state.get("interrupt_payload")
if payload:
    st.markdown("<div class='tj-section-title'>Draft report (editable)</div>", unsafe_allow_html=True)
    st.caption(
        "Review the draft. Edit if needed, fill the report details, "
        "then approve to generate the PDF."
    )

    default_text = st.session_state.get("edited_text") or payload.get("draft_summary", "")
    edited = st.text_area(
        "Report text",
        value=default_text,
        height=200,
        label_visibility="collapsed",
    )

    st.markdown("<div class='tj-section-title'>Citations supporting this report</div>", unsafe_allow_html=True)
    cites = payload.get("draft_citations", [])
    chips = "".join(f"<span class='tj-chip'>{_resolve_preview(c)}</span>" for c in cites)
    st.markdown(chips, unsafe_allow_html=True)

    # ---- Report details form (for the PDF header) ----
    st.markdown("<div class='tj-section-title'>Report details</div>", unsafe_allow_html=True)
    st.caption("These appear on the PDF cover page. Adjust as needed before approving.")

    # Auto-defaults
    latest_term = _latest_term_for_student(selected["student_id"])
    # Reset form defaults whenever the selected student changes
    if st.session_state.get("_details_for_student") != selected["student_id"]:
        st.session_state["_details_for_student"] = selected["student_id"]
        st.session_state["_default_school"] = "Tujifunze Academy"
        st.session_state["_default_class"] = f"Grade {selected['grade_level']}"
        st.session_state["_default_year"] = str(selected["cohort_year"])
        st.session_state["_default_term"] = latest_term
        st.session_state["_default_teacher"] = st.session_state.get("username", "")
        st.session_state["_default_guardian"] = ""
        st.session_state["_default_remarks"] = ""

    with st.form("report_details_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            school_name = st.text_input(
                "School name",
                value=st.session_state["_default_school"],
                placeholder="e.g. Tujifunze Academy",
                help="The full name of the school - appears at the top of the PDF.",
            )
            class_section = st.text_input(
                "Class / Section",
                value=st.session_state["_default_class"],
                placeholder="e.g. Grade 7A",
                help="The class or section the student belongs to.",
            )
            academic_year = st.text_input(
                "Academic year",
                value=st.session_state["_default_year"],
                placeholder="e.g. 2024",
                help="The academic year this report covers.",
            )
            term = st.text_input(
                "Term",
                value=st.session_state["_default_term"],
                placeholder="e.g. Term 3 2024",
                help="Which term this report covers.",
            )
        with c2:
            teacher_name = st.text_input(
                "Teacher name",
                value=st.session_state["_default_teacher"],
                placeholder="e.g. Mr. Faida Sylivester",
                help="Your full name as it should appear on the report.",
            )
            guardian_name = st.text_input(
                "Guardian name (optional)",
                value=st.session_state["_default_guardian"],
                placeholder="e.g. Mrs. Amina Hassan",
                help="Leave blank if this is a teacher-only report.",
            )
            teacher_remarks = st.text_area(
                "Teacher remarks (optional)",
                value=st.session_state["_default_remarks"],
                placeholder="e.g. Amina has had a strong year. I recommend continuing to challenge her with extension problems in Mathematics next term.",
                height=100,
                help="Free-form notes you want to include below the summary.",
            )

        st.form_submit_button("Save details", use_container_width=False)
        # The values are read on Approve click below

    col_a, col_b, _ = st.columns([1, 1, 3])
    with col_a:
        if st.button("Approve & Finalize", type="primary", use_container_width=True):
            # Bundle the form values into session_state so the approved-report
            # section can build the PDF from them.
            st.session_state["pdf_meta"] = {
                "school_name": school_name,
                "class_section": class_section,
                "academic_year": academic_year,
                "term": term,
                "teacher_name": teacher_name,
                "guardian_name": guardian_name,
                "teacher_remarks": teacher_remarks,
                "report_id": payload.get("draft_report_id", "-"),
            }
            _approve_and_finalize(edited)
    with col_b:
        if st.button("Reject", type="secondary", use_container_width=True):
            _reject_draft()

    patterns = payload.get("verified_patterns", [])
    if patterns:
        st.markdown("<div class='tj-section-title'>Verified patterns</div>", unsafe_allow_html=True)
        _render_patterns(patterns)

    if payload.get("verification_warnings"):
        with st.expander("Warnings from verification"):
            for w in payload["verification_warnings"]:
                st.warning(w)


final = st.session_state.get("final_state")
if final and final.get("approved"):
    st.markdown("<div class='tj-section-title'>Approved report</div>", unsafe_allow_html=True)
    final_text = st.session_state.get("edited_text") or final.get("final_text", "")

    st.success(
        f"Report approved by **{final.get('approved_by', 'unknown')}**. "
        "It is now saved to the student's profile."
    )
    st.markdown(
        f"<div class='tj-pattern tj-pattern-strength'>"
        f"<div class='tj-pattern-desc'>{final_text}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ---- Download buttons: PDF and TXT ----
    meta = st.session_state.get("pdf_meta", {})
    try:
        pdf_bytes = generate_pdf_report(
            student_profile=selected,
            summary_text=final_text,
            verified_patterns=final.get("verified_patterns", []) or [],
            citations=final.get("draft_citations", []) or [],
            meta=meta,
        )
        # Build a clean filename that browsers will accept
        safe_name = selected["full_name"].replace(" ", "_").replace("/", "_")
        pdf_filename = f"Tujifunze_Report_{selected['student_id']}_{safe_name}.pdf"
        txt_filename = f"Tujifunze_Report_{selected['student_id']}_{safe_name}.txt"

        # Encode PDF as base64 for a direct, no-round-trip download link.
        b64_pdf = base64.b64encode(pdf_bytes).decode("ascii")
        download_href = f"data:application/pdf;base64,{b64_pdf}"

        dl1, dl2 = st.columns([1, 1])
        with dl1:
            st.markdown(
                f"""
                <a href="{download_href}"
                   download="{pdf_filename}"
                   class="tj-pdf-link"
                   style="display:block;width:100%;text-align:center;
                          padding:0.75rem 1rem;border-radius:10px;
                          background:linear-gradient(135deg,#0d7377 0%,#14a5a9 100%);
                          color:#ffffff !important;font-weight:700;
                          text-decoration:none;font-size:0.95rem;
                          box-shadow:0 2px 8px rgba(13,115,119,0.28);
                          transition:all 0.18s ease;">
                   Download PDF report
                </a>
                <style>
                    .tj-pdf-link:hover {{
                        transform: translateY(-1px);
                        box-shadow: 0 8px 20px rgba(13, 115, 119, 0.38);
                        color: #ffffff !important;
                        text-decoration: none;
                    }}
                </style>
                """,
                unsafe_allow_html=True,
            )
        with dl2:
            st.download_button(
                label="Download text (.txt)",
                data=final_text,
                file_name=txt_filename,
                mime="text/plain",
                use_container_width=True,
                key=f"txt_dl_{selected['student_id']}",
            )
    except Exception as exc:
        st.error(f"PDF generation failed: {exc}")
        st.download_button(
            "Download text (.txt) fallback",
            data=final_text,
            file_name=f"{selected['student_id']}_report.txt",
            mime="text/plain",
        )


with st.expander("Agent debug - raw state"):
    st.write("**Completed nodes:**", st.session_state.get("completed_nodes", []))
    st.write("**Thread config:**", st.session_state.get("thread_config"))
    st.write("**Interrupt payload:**", st.session_state.get("interrupt_payload"))
    st.write("**Final state:**", st.session_state.get("final_state"))
