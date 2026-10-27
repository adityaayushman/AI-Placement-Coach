# AI Placement Coach

AI-driven platform that evaluates an engineering student's placement readiness and gives personalized, continuously updated guidance. Full spec: [placement plan](placement%20plan). Working agreements: [CLAUDE.md](CLAUDE.md). Decisions: [docs/DECISIONS.md](docs/DECISIONS.md).

## Architecture

```
 Vercel                      Render
┌───────────┐  HTTPS   ┌────────────┐   ┌────────────┐
│ React SPA │─────────▶│ FastAPI    │──▶│ PostgreSQL │
│ (Vite)    │          │ API        │   └────────────┘
└───────────┘          └─────┬──────┘   ┌────────────┐
                             │ enqueue  │ Redis      │
                       ┌─────▼──────┐──▶│ (RQ)       │
                       │ RQ worker  │   └────────────┘
                       └────────────┘
```

Local development uses Docker Compose with the same five pieces (api, worker, db, redis, web).

## Setup and run

**Docker (everything):**
```
cp .env.example .env
docker compose up --build
```
API: http://localhost:8000/api/v1/health (readiness: `/api/v1/ready`, docs: `/docs`). Web: http://localhost:5173.

**Without Docker:**
```
cd backend && python -m venv .venv && .venv/Scripts/activate   # Windows; use bin/activate elsewhere
pip install -e ".[dev]" && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev                      # dev server on :5173
```

## Test and lint

```
cd backend  && ruff check . && ruff format --check . && mypy app && pytest
cd frontend && npm run lint && npm run typecheck && npm test && npm run build
```
CI (`.github/workflows/ci.yml`) runs the same commands.

## Deployment (not yet performed)

- Backend on Render: `render.yaml` Blueprint (API, worker, Postgres, Key Value). Set `CORS_ORIGINS` to the Vercel URL.
- Frontend on Vercel: root directory `frontend`, env `VITE_API_URL` = Render API URL.

## Phase status

| Phase | Scope | Status |
|---|---|---|
| 0 | Foundations | done, awaiting review |
| 1 | Auth, data model, consent | not started |
| 2 | Resume pipeline | not started |
| 3 | Assessments and activity | not started |
| 4 | Readiness predictor | not started |
| 5 | Mock interview | not started |
| 6 | Recommendation engine | not started |
| 7 | Aggregator and dashboards | not started |
| 8 | Evaluation and pilot harness | not started |
| 9 | Hardening and release | not started |
