# Troubleshooting

| Symptom | Fix |
|---------|-----|
| API won't start / DB connection | Ensure Postgres is up; check `DATABASE_URL` |
| Login fails after seed | Run `python -m app.scripts.seed`; use `demo@student.edu` / `DemoPass123!` |
| AI tutor says unavailable | Set `AI_API_KEY` (and optional `AI_BASE_URL`) |
| Document stuck Processing | Check API logs; unsupported/empty files mark Failed |
| Chroma connection errors | App falls back to local `./data/chroma`; ensure write permissions |
| CORS errors in browser | Add frontend origin to `CORS_ORIGINS` |
| Frontend 401 loops | Clear localStorage token and log in again |

Logs: structured lines on stdout (`event key=value`). Passwords and API keys are never logged.
