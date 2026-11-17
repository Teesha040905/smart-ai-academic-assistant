# Deployment Guide

Production setup (all free tiers):

| Part | Host | Notes |
|---|---|---|
| Frontend (Next.js) | **Vercel** | Deploys automatically on every push to `main` |
| Backend (FastAPI, Docker) | **Render** | Deploys automatically after GitHub Actions CI passes |
| Database | **MongoDB Atlas** (M0 free, 512 MB) | Also stores uploaded files (GridFS) and document search vectors |

```
Browser ──► Vercel (frontend) ──► Render (backend API) ──► MongoDB Atlas
```

Do the steps in this order: **Atlas → Render → Vercel → update Render CORS**.

---

## 1. MongoDB Atlas

1. Sign up at <https://www.mongodb.com/cloud/atlas> and create a free **M0** cluster (region: Mumbai `ap-south-1` or Singapore).
2. **Database Access** → *Add New Database User* → username + strong password (role: *Read and write to any database*).
3. **Network Access** → *Add IP Address* → `0.0.0.0/0` (Render's free tier has no fixed IP, so this is required).
4. **Connect** → *Drivers* → copy the connection string, e.g.
   `mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`
   Replace `<password>` with the real password (URL-encode special characters like `@` → `%40`).

## 2. Backend on Render

1. Sign up at <https://render.com> with your GitHub account.
2. **New → Blueprint** → select the `smart-ai-academic-assistant` repository. Render reads `render.yaml`.
3. It asks for the secret values:
   | Variable | Value |
   |---|---|
   | `MONGODB_URL` | the Atlas connection string from step 1 |
   | `AI_API_KEYS` | your Gemini API key(s), comma-separated |
   | `FRONTEND_URL` | put `https://example.com` for now (fixed in step 4) |
   | `CORS_ORIGINS` | put `https://example.com` for now (fixed in step 4) |
   `JWT_SECRET` is generated automatically.
4. Click **Apply**. When the deploy finishes, open
   `https://<your-service>.onrender.com/health` → it should show `"db_status":"ok"`.
   API docs: `https://<your-service>.onrender.com/docs`.

## 3. Frontend on Vercel

1. Sign up at <https://vercel.com> with your GitHub account.
2. **Add New → Project** → import the repository.
3. **Root Directory**: `frontend` (Framework is detected as Next.js).
4. **Environment Variables**:
   | Variable | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://<your-service>.onrender.com/api/v1` |
5. **Deploy**. You get a URL like `https://smart-ai-academic-assistant.vercel.app`.

## 4. Connect them (CORS)

Render → your service → **Environment** → set both to your Vercel URL (no trailing slash):

- `FRONTEND_URL` = `https://smart-ai-academic-assistant.vercel.app`
- `CORS_ORIGINS` = `https://smart-ai-academic-assistant.vercel.app`

Save → Render redeploys. Open the Vercel URL, register and log in. Done.

Optional: to let Vercel *preview* deployments (one per pull request) talk to the backend, set
`CORS_ORIGIN_REGEX` = `https://smart-ai-academic-assistant-.*\.vercel\.app`.

---

## CI/CD

`.github/workflows/ci.yml` runs on every push and pull request to `main`:

1. **Backend tests**: pytest against a temporary MongoDB.
2. **Frontend build**: `npm run lint` + `npm run build`.
3. **Docker images build**: checks both Dockerfiles still build.

Deploys:
- **Render** (`autoDeployTrigger: checksPass`) deploys the backend only when CI passes, and only when files in `backend/` changed.
- **Vercel** deploys the frontend on every push to `main`, and creates a preview URL for every pull request.

No GitHub secrets are required.

## Things to know about the free tiers

- **Render free sleeps after 15 minutes without traffic.** The first request after that takes ~50 seconds. Open the backend `/health` URL a minute before a demo/viva to wake it up.
- Atlas M0 has 512 MB. Uploaded files are stored in it, so the upload limit is set to 15 MB (`MAX_UPLOAD_MB`).
- Changing a `NEXT_PUBLIC_*` variable on Vercel needs a **Redeploy** (it is built into the frontend).

## Run the production setup locally with Docker

```bash
cp .env.example .env      # set JWT_SECRET (32+ chars) and AI_API_KEYS
docker compose up --build
```
Frontend <http://localhost:3000>, API <http://localhost:8000/docs>.

## Environment variables reference

See `.env.example` (backend) and `frontend/.env.local.example` (frontend). Production-only settings:

| Variable | Production value | Why |
|---|---|---|
| `ENVIRONMENT` | `production` | Strict CORS; refuses to start with a weak `JWT_SECRET` |
| `FILE_STORAGE` | `gridfs` | Render's disk is wiped on every restart/deploy |
| `VECTOR_STORE` | `mongo` | Document search index survives restarts |
