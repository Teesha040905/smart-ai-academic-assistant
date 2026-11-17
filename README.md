# Smart AI Academic Assistant

Production-oriented full-stack academic assistant with RAG tutoring, adaptive study planning, quizzes, flashcards, and explainable recommendations.

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Backend | FastAPI, PyMongo, Pydantic v2 |
| Database | MongoDB 7 |
| Vector store | ChromaDB (user-isolated metadata filtering) |
| Auth | JWT access tokens + bcrypt password hashing |
| AI | OpenAI-compatible API (`AI_API_KEY`, `AI_BASE_URL`) |
| Jobs | Background document processing worker |
| Infra | Docker Compose |

## Quick start

### Prerequisites

- Docker Desktop **or** Node 20+, Python 3.11+, PostgreSQL 16
- An OpenAI-compatible API key (optional for non-AI features; required for tutor/quiz/RAG)

### With Docker (recommended)

```bash
cp .env.example .env
# Edit .env — set JWT_SECRET and AI_API_KEY

docker compose up --build
```

- Frontend: http://localhost:3000  
- API docs: http://localhost:8000/docs  
- Demo login: `demo@student.edu` / `DemoPass123!`

### Local development

```bash
# Backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
python -m app.scripts.seed
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

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
