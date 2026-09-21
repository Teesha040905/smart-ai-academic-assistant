# Testing

```bash
cd backend
pip install -r requirements.txt
pytest -q
```

Coverage includes:

- Registration / login / invalid credentials
- Protected routes
- Subject CRUD + progress
- Cross-user isolation
- Recommendation urgency for weak topics near exams
- Quiz generation fallback without AI key
- Invalid upload rejection

Add RAG integration tests once Chroma + sample PDF fixtures are available in CI.
