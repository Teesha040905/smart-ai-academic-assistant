# Smart AI Academic Assistant

Production-oriented full-stack academic assistant with RAG tutoring, adaptive study planning, quizzes, flashcards, and explainable recommendations.

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Backend | FastAPI, PyMongo, Pydantic v2 |
| Database | MongoDB 7 |
| Vector store | MongoDB (default in production) or ChromaDB, user-isolated filtering |
| Auth | JWT access tokens + bcrypt password hashing |
| AI | OpenAI-compatible API (`AI_API_KEY`, `AI_BASE_URL`) |
| Jobs | Background document processing worker |
| Infra | Docker, GitHub Actions CI, Vercel (frontend) + Render (backend) + MongoDB Atlas |

## Quick start

### Prerequisites

- Docker Desktop **or** Node 20+, Python 3.12+, MongoDB 7+
- An OpenAI-compatible API key (optional for non-AI features; required for tutor/quiz/RAG)

### With Docker (recommended)

```bash
cp .env.example .env
# Edit .env — set JWT_SECRET (32+ chars) and AI_API_KEYS

docker compose up --build
```

- Frontend: http://localhost:3000  
- API docs: http://localhost:8000/docs  
- Optional demo data: `docker compose exec api python -m app.scripts.seed` (login `demo@student.edu` / `DemoPass123!`)

### Local development

```bash
# Backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp ../.env.example ../.env
python -m app.scripts.seed
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## Deployment

Live deployment (Vercel + Render + MongoDB Atlas, all free tiers) and CI/CD are described step by step in [docs/deployment.md](docs/deployment.md).

To learn AWS, the app can also run on a single EC2 server with Docker and automatic HTTPS: [docs/deploy-aws.md](docs/deploy-aws.md).

## Demo scenario

Seeded student (B.Tech Computer Engineering, Semester 6):

- Subjects: Machine Learning, AI, SPM, Mobile Communication  
- ML exam in ~6 days  
- Weak topics: Backpropagation, GAN  
- Dashboard shows deterministic AI recommendations driven by quiz scores + exam urgency  

## Documentation

- [Architecture](docs/architecture.md)
- [Database](docs/database.md)
- [API](docs/api.md)
- [AI & RAG](docs/ai.md)
- [Recommendation engine](docs/recommendations.md)
- [Deployment](docs/deployment.md)
- [Testing](docs/testing.md)
- [Troubleshooting](docs/troubleshooting.md)

## Privacy

Uploaded documents are used only to answer your questions and generate study aids. You can delete documents and account data from Settings. See Settings → Privacy in the app.

## License

Educational / project use.
