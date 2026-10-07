from pathlib import Path

p = Path("app.py")
text = p.read_text(encoding="utf-8")

anchor = """load_dotenv(override=True)

import hmac"""

replacement = """load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Auto-seed the SQLite database on first run.
# The DB file is git-ignored, so it must be regenerated in any fresh
# environment (local machine, Streamlit Cloud cold start, etc.).
# ---------------------------------------------------------------------------
def _ensure_database() -> None:
    from pathlib import Path as _P
    import subprocess
    import sys as _sys

    project_root = _P(__file__).resolve().parent
    db_path = project_root / "data" / "tujifunze_data.db"

    if not db_path.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [_sys.executable, str(project_root / "scripts" / "init_db.py")],
            cwd=str(project_root),
            check=True,
        )

_ensure_database()

import hmac"""

if "_ensure_database" in text:
    print("SKIP: auto-seed already present")
elif anchor not in text:
    print("ERROR: anchor 'load_dotenv(override=True)\\n\\nimport hmac' not found")
else:
    text = text.replace(anchor, replacement, 1)
    p.write_text(text, encoding="utf-8")
    print("OK: auto-seed inserted")
