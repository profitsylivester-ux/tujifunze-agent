# Tujifunze Agent

**Longitudinal learning insights for educators - sourced, verified, teacher-approved.**

A teacher-supervised agentic AI that reads a student's multi-term academic,
attendance, and qualitative observation records, surfaces **cited patterns**,
and drafts a **plain-language report** - with a mandatory human approval gate
before anything is finalized.

Built for the African Agentic AI Design Challenge - Education track.
https://agentic-africa-challenge.lovable.app

---

## Live Demo

- **App:** https://tujifunze-agent.streamlit.app
- **Repo:** https://github.com/profitsylivester-ux/tujifunze-agent

**Login:**
- Username: teacher
- Password: tujifunze2024

**Try it:**
1. Pick a student from the sidebar
2. Click "Run Agent Analysis"
3. Watch the 5-node agent pipeline execute live
4. Review the draft report - every claim carries citations back to real records
5. Edit the draft, add your own teacher remarks
6. Approve to generate the PDF report

---

## The Problem

Teachers in African schools accumulate **three parallel streams of evidence**
about every learner, across multiple terms:

- Academic scores (quizzes, tests, exams, assignments)
- Attendance registers (present / late / absent)
- Qualitative teacher observation notes

These live in separate spreadsheets, notebooks, or paper files. No educator
has time to read three terms of fragmentary data and form a coherent, defensible
view of a child's trajectory. And the moment you ask an LLM to summarize that
data, you risk **hallucinated claims** and **fixed labels** about a child
("this student is weak at math" / "she will be an engineer") - both are
unacceptable in an educational setting.

**Tujifunze Agent solves this by design.**

---

## The Non-Negotiable Rule

> **The agent MUST NOT assign fixed track or career labels to a child.
> It surfaces only sourced, defensible patterns, and every report requires
> a teacher's explicit approval before it is finalized.**

This rule is enforced at three layers:

1. **Tool layer** - flag_learning_pattern() rejects any pattern whose
   citations do not resolve to real records in the database.
2. **Agent layer** - the analysis prompt forbids labels and requires
   at least 2 source citations per pattern.
3. **Human layer** - the LangGraph workflow pauses at an interrupt() gate
   and cannot complete without a teacher clicking Approve.

---

## Tech Stack (all open-source)

| Layer | Tool | Purpose |
|-------|------|---------|
| Orchestration | LangGraph | 5-node state machine with checkpointing |
| LLM (cloud) | Qwen 3.8 27B via Groq | Analysis and report drafting |
| LLM (local) | Qwen 2.5 3B via Ollama | Offline / privacy-first mode |
| Protocol | MCP (Model Context Protocol) | Standard tool interface |
| Tools | Custom Python MCP Server | 3 domain-specific tools |
| Database | SQLite | Single-file persistent store |
| UI | Streamlit | Teacher dashboard |
| PDF | ReportLab | Plain-language printable report |
| Validation | Pydantic | Schema enforcement |

---

## The Three MCP Tools

Exposed over stdio in `mcp_server/custom_server.py`:

### 1. get_student_historical_records(student_id)
Returns the full longitudinal record: profile, scores by term and subject,
attendance summary, and teacher observations. Every record carries a
citation_id (e.g. score:14, observation:2) used by downstream tools.

### 2. flag_learning_pattern(student_id, pattern_type, description, source_citations)
Persists a **verified** pattern to the student's profile. Rejects the call
if any citation does not resolve to a real record belonging to that student.
pattern_type must be one of: strength, struggle, emerging, attendance_concern.

### 3. draft_plain_language_report(student_id, summary_text, citations)
Stores a plain-language draft with citations. Starts in status=draft
and can only move to approved via the human-in-the-loop gate.

Plus a helper: list_students() for populating the sidebar.

---

## The Five LangGraph Nodes

| # | Node | What it does |
|---|------|--------------|
| 1 | retrieve | Fetches the full student record from SQLite |
| 2 | analyze | LLM identifies sourced patterns (strengths, struggles, emerging) |
| 3 | verify | Cross-references every citation against the DB; drops unsourced claims |
| 4 | report | LLM writes a jargon-free summary grounded in the verified patterns |
| 5 | hitl | Interrupts the graph and hands control to the teacher |

The graph is compiled with a MemorySaver checkpointer so the interrupt
can pause and later resume with the teacher's decision.

The Human-in-the-Loop gate is implemented via LangGraph's interrupt()
primitive. When the graph reaches the hitl node, it pauses execution and
returns the draft payload to the caller. Streamlit displays that payload
to the teacher, who edits it, adds their own remarks, and clicks
Approve and Finalize. The graph then resumes with the teacher's decision.

Nothing is saved, exported, or finalized without that click.

---

## Run Locally

Requires Python 3.11 on Windows.

    git clone https://github.com/profitsylivester-ux/tujifunze-agent.git
    cd tujifunze-agent
    py -3.11 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt

Create a .env file with your LLM backend:

    LLM_BACKEND=groq
    GROQ_API_KEY=gsk_your_key_here
    GROQ_MODEL=qwen/qwen3.8-27b

Then run:

    streamlit run app.py

The app auto-seeds the SQLite database on first run, so no manual
database setup is required.

---

## Deploy to Streamlit Cloud

1. Push the repo to GitHub.
2. Go to https://share.streamlit.io and create a new app.
3. Select repo profitsylivester-ux/tujifunze-agent, branch main, file app.py.
4. In Advanced settings, add the same secrets as the .env file above.
5. Deploy.

---

## Project Structure

    tujifunze-agent/
      app.py                      Streamlit teacher dashboard
      requirements.txt
      agent/
        graph.py                  LangGraph 5-node state machine
        llm.py                    Ollama / Groq backend switcher
      mcp_server/
        custom_server.py          MCP server exposing the 3 tools
      tools/
        db.py                     SQLite connection helper
        get_records.py            Tool 1: get_student_historical_records
        flag_pattern.py           Tool 2: flag_learning_pattern
        draft_report.py           Tool 3: draft_plain_language_report
        citation_resolver.py      Turns score:14 into a readable label
        pdf_report.py             ReportLab PDF generator
      scripts/
        init_db.py                Seeds the SQLite DB with sample data
      data/
        tujifunze_data.db         Auto-generated on first run

---

## License

MIT

---

## Author

Faida Sylivester
GitHub: https://github.com/profitsylivester-ux

Built for the African Agentic AI Design Challenge, Education track.
