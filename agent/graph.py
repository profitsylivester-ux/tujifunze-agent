"""
Tujifunze agent graph.

A LangGraph state machine with 5 nodes:

  1. retrieve   -> pulls the student's full historical record
  2. analyze    -> asks the LLM to identify sourced patterns (strengths/struggles)
  3. verify     -> cross-references every pattern's citations against the DB
  4. report     -> asks the LLM to write a plain-language summary
  5. hitl       -> HUMAN-IN-THE-LOOP GATE (interrupts before finalizing)

The graph is compiled with a checkpointer so the interrupt can pause
execution and be resumed from the Streamlit UI.
"""

from __future__ import annotations

import json
import re
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from agent.llm import get_llm
from tools.draft_report import draft_plain_language_report
from tools.flag_pattern import flag_learning_pattern
from tools.get_records import get_student_historical_records


# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------

class AgentState(TypedDict, total=False):
    student_id: str
    student_record: dict[str, Any]      # raw output of get_student_historical_records
    proposed_patterns: list[dict]       # [{pattern_type, description, source_citations}]
    verified_patterns: list[dict]       # only the ones whose citations resolved
    flagged_pattern_ids: list[int]      # IDs written to flagged_patterns table
    draft_summary: str                  # plain-language summary text
    draft_citations: list[str]          # citation IDs supporting the summary
    draft_report_id: int                # ID of the row in draft_reports
    verification_warnings: list[str]    # things that got dropped/flagged
    approved: bool                      # set by the HITL gate
    approved_by: str                    # teacher name from the UI
    final_text: str                     # what the teacher approved (or edited)
    errors: list[str]


# ---------------------------------------------------------------------------
# Node 1: Retrieve
# ---------------------------------------------------------------------------

def node_retrieve(state: AgentState) -> AgentState:
    """Pull the full student record from the database."""
    sid = state["student_id"]
    record = get_student_historical_records(sid)

    if "error" in record:
        return {
            **state,
            "student_record": {},
            "errors": state.get("errors", []) + [f"Retrieval failed: {record['error']}"],
        }

    return {**state, "student_record": record}


# ---------------------------------------------------------------------------
# Node 2: Analyze
# ---------------------------------------------------------------------------

ANALYSIS_SYSTEM_PROMPT = """You are an education analyst reviewing a single student's
longitudinal record across multiple terms.

Your job: identify UP TO 4 clear, defensible patterns — strengths, struggles,
emerging changes, or attendance concerns — that are supported by the data.

STRICT RULES:
1. Never assign a fixed label, track, or career verdict to the student.
   Bad: "She is a future engineer." Bad: "He is weak at math."
   Good: "Her Math scores rose from 70% to 90% across Terms 1-3."
2. Every pattern MUST cite at least two real citation IDs from the record.
   Citation IDs look like "score:14" or "observation:2".
3. Keep descriptions observational and specific.

Return ONLY a JSON array. Each element must have:
  - pattern_type: one of "strength", "struggle", "emerging", "attendance_concern"
  - description: one or two plain sentences
  - source_citations: array of citation IDs (strings)

Example output:
[
  {
    "pattern_type": "strength",
    "description": "Math scores rose consistently from 70% in Term 1 to 90% in Term 3.",
    "source_citations": ["score:1", "score:49"]
  }
]

Return the JSON array and nothing else. No prose, no markdown fences.
"""


def node_analyze(state: AgentState) -> AgentState:
    """Ask the LLM to identify sourced patterns from the student record."""
    if not state.get("student_record"):
        return {**state, "proposed_patterns": []}

    llm = get_llm(temperature=0.1)

    record = state["student_record"]
    # Only send the model what it needs — keeps the prompt small and fast.
    compact = {
        "profile": record["profile"],
        "scores_by_term": record["scores_by_term"],
        "attendance_by_term": record["attendance_by_term"],
        "observations": [
            {
                "citation_id": o["citation_id"],
                "term": o["term"],
                "date": o["date"],
                "note": o["note"],
            }
            for o in record["observations"]
        ],
    }

    messages = [
        SystemMessage(content=ANALYSIS_SYSTEM_PROMPT),
        HumanMessage(
            content="Student record (JSON):\n\n" + json.dumps(compact, indent=2)
        ),
    ]

    try:
        response = llm.invoke(messages)
        raw = response.content if isinstance(response.content, str) else str(response.content)
        patterns = _parse_patterns_json(raw)
    except Exception as exc:  # noqa: BLE001
        return {
            **state,
            "proposed_patterns": [],
            "errors": state.get("errors", []) + [f"Analysis failed: {exc}"],
        }

    return {**state, "proposed_patterns": patterns}


def _parse_patterns_json(raw: str) -> list[dict]:
    """LLMs sometimes wrap JSON in fences or add prose. Be forgiving."""
    raw = raw.strip()
    # Strip markdown fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    # Find the outermost [ ... ]
    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1 or end < start:
        return []

    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    cleaned: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        ptype = item.get("pattern_type", "").strip()
        desc = (item.get("description") or "").strip()
        cites = item.get("source_citations") or []
        if not isinstance(cites, list):
            cites = []
        cites = [c for c in cites if isinstance(c, str) and ":" in c]
        if ptype and desc and cites:
            cleaned.append(
                {
                    "pattern_type": ptype,
                    "description": desc,
                    "source_citations": cites,
                }
            )
    return cleaned


# ---------------------------------------------------------------------------
# Node 3: Verify (citation cross-check)
# ---------------------------------------------------------------------------

def node_verify(state: AgentState) -> AgentState:
    """
    Write each proposed pattern via flag_learning_pattern. The tool itself
    rejects anything whose citations don't resolve — so we just collect
    successes and record warnings for the rest.
    """
    sid = state["student_id"]
    verified: list[dict] = []
    flagged_ids: list[int] = []
    warnings: list[str] = list(state.get("verification_warnings", []))

    for p in state.get("proposed_patterns", []):
        result = flag_learning_pattern(
            student_id=sid,
            pattern_type=p["pattern_type"],
            description=p["description"],
            source_citations=p["source_citations"],
        )
        if result.get("status") == "ok":
            verified.append(p)
            flagged_ids.append(result["pattern_id"])
        else:
            warnings.append(
                f"Dropped pattern ({p['pattern_type']}): {result.get('message', result)}"
            )

    return {
        **state,
        "verified_patterns": verified,
        "flagged_pattern_ids": flagged_ids,
        "verification_warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Node 4: Report (plain-language draft)
# ---------------------------------------------------------------------------

REPORT_SYSTEM_PROMPT = """You write plain-language summaries for teachers and guardians.

Rules:
1. Write in simple, jargon-free language. Imagine a busy teacher reading it in 30 seconds.
2. Never assign a track, career, or verdict. Describe only what the data shows.
3. Reference the observable trajectory (upward, downward, steady) and attendance.
4. End with one short sentence naming what the teacher might focus on next.
5. Do NOT include citation IDs in the text — they will be attached separately.

Return ONLY the summary paragraph. No headers, no JSON, no markdown.
"""


def node_report(state: AgentState) -> AgentState:
    """Generate a plain-language summary grounded in the verified patterns."""
    record = state.get("student_record", {})
    if not record:
        return {**state, "draft_summary": "", "draft_citations": []}

    llm = get_llm(temperature=0.3)

    patterns = state.get("verified_patterns", [])
    if not patterns:
        # Fall back to a minimal summary citing nothing — but never call draft_report
        return {
            **state,
            "draft_summary": "",
            "draft_citations": [],
            "errors": state.get("errors", [])
            + ["No verified patterns; skipping report draft."],
        }

    # Collect every citation used across verified patterns
    all_citations: list[str] = []
    for p in patterns:
        for c in p["source_citations"]:
            if c not in all_citations:
                all_citations.append(c)

    profile = record["profile"]
    patterns_text = "\n".join(
        f"- [{p['pattern_type']}] {p['description']}" for p in patterns
    )

    messages = [
        SystemMessage(content=REPORT_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Student: {profile['full_name']}, Grade {profile['grade_level']}\n"
                f"Cohort year: {profile['cohort_year']}\n\n"
                f"Verified patterns:\n{patterns_text}\n\n"
                f"Write the plain-language summary."
            )
        ),
    ]

    try:
        response = llm.invoke(messages)
        summary = response.content if isinstance(response.content, str) else str(response.content)
        summary = summary.strip()
    except Exception as exc:  # noqa: BLE001
        return {
            **state,
            "draft_summary": "",
            "draft_citations": [],
            "errors": state.get("errors", []) + [f"Report generation failed: {exc}"],
        }

    # Persist the draft via the tool
    stored = draft_plain_language_report(
        student_id=state["student_id"],
        summary_text=summary,
        citations=all_citations,
    )

    if stored.get("status") != "ok":
        return {
            **state,
            "draft_summary": summary,
            "draft_citations": all_citations,
            "errors": state.get("errors", [])
            + [f"Draft storage failed: {stored}"],
        }

    return {
        **state,
        "draft_summary": summary,
        "draft_citations": all_citations,
        "draft_report_id": stored["report_id"],
    }


# ---------------------------------------------------------------------------
# Node 5: Human-in-the-loop gate
# ---------------------------------------------------------------------------

def node_hitl(state: AgentState) -> AgentState:
    """
    Pause for teacher approval.

    `interrupt()` suspends the graph here and returns control to the caller
    (Streamlit). The caller resumes with a value that becomes the return of
    interrupt(). We expect that value to be a dict like:
        {"approved": True, "approved_by": "JM", "final_text": "..."}
    """
    payload = {
        "draft_report_id": state.get("draft_report_id"),
        "student_id": state.get("student_id"),
        "draft_summary": state.get("draft_summary", ""),
        "draft_citations": state.get("draft_citations", []),
        "verified_patterns": state.get("verified_patterns", []),
        "verification_warnings": state.get("verification_warnings", []),
        "errors": state.get("errors", []),
    }

    decision = interrupt(payload)

    # `decision` is whatever the UI passes back on resume.
    if not isinstance(decision, dict):
        decision = {"approved": False}

    return {
        **state,
        "approved": bool(decision.get("approved", False)),
        "approved_by": str(decision.get("approved_by", "")).strip(),
        "final_text": str(decision.get("final_text", state.get("draft_summary", ""))).strip(),
    }


# ---------------------------------------------------------------------------
# Graph wiring
# ---------------------------------------------------------------------------

def build_graph():
    """Build and compile the Tujifunze agent graph with an in-memory checkpointer."""
    g = StateGraph(AgentState)

    g.add_node("retrieve", node_retrieve)
    g.add_node("analyze", node_analyze)
    g.add_node("verify", node_verify)
    g.add_node("report", node_report)
    g.add_node("hitl", node_hitl)

    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "analyze")
    g.add_edge("analyze", "verify")
    g.add_edge("verify", "report")
    g.add_edge("report", "hitl")
    g.add_edge("hitl", END)

    checkpointer = MemorySaver()
    return g.compile(checkpointer=checkpointer)


# Module-level compiled graph for easy import
graph = build_graph()
