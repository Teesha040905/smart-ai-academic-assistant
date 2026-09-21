# Deployment

## Docker Compose

```bash
cp .env.example .env
# set JWT_SECRET and AI_API_KEY
docker compose up --build
```

Services: `frontend` (:3000), `api` (:8000), `db` (Postgres), `chroma`, `redis`.

## Production checklist

- Strong unique `JWT_SECRET`
- TLS termination (nginx/Caddy/cloud LB)
- Managed Postgres + backups
- Persistent volumes for `uploads` and Chroma
- Restrict CORS to real frontend origin
- Set `ENVIRONMENT=production`, `DEBUG=false`
- Rotate `AI_API_KEY` via secret manager
- Add rate limiting at gateway
- Run Alembic migrations instead of create_all

## Scaling

- Stateless API replicas behind a load balancer
- Shared Postgres + Chroma/pgvector
- Move `process_document_job` to a Redis/RQ or Celery worker consuming the same code path
