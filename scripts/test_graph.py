"""
End-to-end test of the Tujifunze agent graph.

Uses graph.stream() so the HITL interrupt() actually fires.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langgraph.types import Command
from agent.graph import graph


def run_for_student(student_id: str) -> None:
    print(f"\n{'='*70}")
    print(f"Running agent for student: {student_id}")
    print(f"{'='*70}\n")

    config = {"configurable": {"thread_id": f"test-{student_id}"}}

    print("--- Streaming graph (will pause at HITL gate) ---")
    last_state = None
    interrupt_payload = None

    # graph.stream yields (chunk, mode) or just chunk depending on stream_mode.
    for chunk in graph.stream(
        {"student_id": student_id, "errors": []},
        config=config,
        stream_mode="updates",
    ):
        # chunk is a dict: {node_name: state_updates} OR {"__interrupt__": (...)}
        if "__interrupt__" in chunk:
            interrupts = chunk["__interrupt__"]
            interrupt_payload = interrupts[0].value
            print("\n>>> Interrupt fired <<<\n")
            break
        for node_name, update in chunk.items():
            print(f"[node: {node_name}] completed")

    if interrupt_payload is None:
        print("No interrupt fired — check graph wiring.")
        return

    print("--- HITL gate reached. Agent is paused. ---\n")
    print("Draft report ID:", interrupt_payload["draft_report_id"])
    print("\nDraft summary:\n")
    print(interrupt_payload["draft_summary"])
    print("\nCitations:", interrupt_payload["draft_citations"])
    print(f"\nVerified patterns: {len(interrupt_payload['verified_patterns'])}")
    for p in interrupt_payload["verified_patterns"]:
        print(f"  [{p['pattern_type']}] {p['description']}")
        print(f"      cites: {p['source_citations']}")

    if interrupt_payload.get("verification_warnings"):
        print("\nWarnings:")
        for w in interrupt_payload["verification_warnings"]:
            print(f"  - {w}")

    print("\n--- Resuming with approval ---\n")
    decision = {
        "approved": True,
        "approved_by": "JM",
        "final_text": interrupt_payload["draft_summary"],
    }
    for chunk in graph.stream(
        Command(resume=decision),
        config=config,
        stream_mode="updates",
    ):
        for node_name, update in chunk.items():
            print(f"[node: {node_name}] completed")
            last_state = update

    print("\nFinal approved state:")
    if last_state:
        print("  approved:   ", last_state.get("approved"))
        print("  approved_by:", last_state.get("approved_by"))


if __name__ == "__main__":
    sid = sys.argv[1] if len(sys.argv) > 1 else "S004"
    run_for_student(sid)
