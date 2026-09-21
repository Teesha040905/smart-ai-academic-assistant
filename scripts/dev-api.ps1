# Local development helpers (PowerShell)

# Backend
cd "$PSScriptRoot\..\backend"
.\.venv\Scripts\python -m app.scripts.seed
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
