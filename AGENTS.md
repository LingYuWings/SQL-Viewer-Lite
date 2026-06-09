# AGENTS.md

## Project

SQL-Viewer Lite — lightweight MySQL data viewer/editor, PyQt5 desktop app.

## Tech Stack

- Python 3.8+, PyQt5, PyMySQL, QSS
- Entry point: `main.py`
- Package: `sql_viewer_lite/` → `ui/` `core/` `models/` `utils/` `backend/` `tests/`

## Dev Commands

```
pip install -r requirements.txt
pytest
black .
```

## Conventions

- PEP 8 + `black` formatter
- Type hints on core modules
- Use `logging` module, not `print()`
- Catch `pymysql.Error` on all DB ops, show friendly messages
- Config stored at `~/.sql_viewer_lite/`

## Planning Docs

- `SPEC.md` — feature spec and architecture
- `PLAN.md` — milestones and phasing
- `TASK.md` — task checklist (update status marks as you work)
