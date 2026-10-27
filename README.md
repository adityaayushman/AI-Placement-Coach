# AI Placement Coach

AI-driven platform that evaluates an engineering student's placement readiness and gives personalised, continuously updated guidance. Full spec: [placement plan](placement%20plan). Working agreements: [CLAUDE.md](CLAUDE.md). Decisions and deviations: [docs/DECISIONS.md](docs/DECISIONS.md).

**Live frontend:** https://ai-placement-coach-murex.vercel.app . The backend is not deployed yet, so sign-in does not work there until Render is set up ([docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)). Use the **Preview as student / coordinator / admin** buttons to explore every screen with clearly labelled sample data.

## What it does

| Module | Implementation |
|---|---|
| Readiness predictor | Logistic regression, random forest and gradient boosting compared by 5-fold stratified CV, best model Platt-calibrated, versioned registry, per-prediction attributions |
| Resume and skill-gap analyser | PDF/DOCX/TXT parsing, section detection, taxonomy skill extraction with fuzzy fallback, explainable ATS rules with fixes, JD text match, gaps ranked by role and company-type weight |
| Mock interview | HR, behavioural, technical and DSA questions; text or recorded answers; prosody from WAV (pace, pauses, pitch variation); content, communication and delivery sub-scores with specific feedback |
| Recommendations | Bayesian Knowledge Tracing per skill; ranking by gap × weight × prerequisite readiness with diversity and a reason string; accept / complete / skip feeds back |
| Readiness score | Weighted blend of the five components, weights stored with each score, history and change since last time; new data triggers a rescore |
| Governance | Per-scope consent with revocation, data export (JSON/CSV) and hard delete, audit log, coordinator aggregates with small-group suppression |

Model training data is **synthetic** until pilot data exists. The UI and [docs/EVALUATION.md](docs/EVALUATION.md) say so wherever it matters.

## Architecture

```
 Vercel                      Render
┌───────────┐  HTTPS   ┌────────────┐   ┌────────────┐
│ React SPA │─────────▶│ FastAPI    │──▶│ PostgreSQL │
│ (Vite)    │          │ API + ML   │   └────────────┘
└───────────┘          └─────┬──────┘   ┌────────────┐
                             │ enqueue  │ Redis      │
                       ┌─────▼──────┐──▶│ (RQ)       │
                       │ RQ worker  │   └────────────┘
                       └────────────┘
```

Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). API reference: [docs/API.md](docs/API.md).

## Setup and run

**Docker (everything):**
```
cp .env.example .env            # set ADMIN_EMAIL / ADMIN_PASSWORD for an admin account
docker compose up --build
```
API: http://localhost:8000/docs. Web: http://localhost:5173. Sign up as a student, or sign in as the admin to create coordinators.

**Without Docker** (SQLite, no Redis):
```
cd backend
python -m venv .venv && .venv/Scripts/activate        # bin/activate on macOS/Linux
pip install -e ".[dev]"
set DATABASE_URL=sqlite:///./demo.db& set JOBS_INLINE=true& uvicorn app.main:app --reload
cd ../frontend && npm install && npm run dev
```

## Test, lint, evaluate

```
cd backend  && ruff check . && ruff format --check . && mypy app && pytest
cd frontend && npm run lint && npm run typecheck && npm test && npm run build
cd backend  && python ../scripts/evaluate.py          # regenerates docs/EVALUATION.md
python scripts/load_smoke.py http://127.0.0.1:8000    # p95 latency check on a running API
```
CI (`.github/workflows/ci.yml`) runs the lint, type and test commands.

## Phase status

| Phase | Scope | Status |
|---|---|---|
| 0 | Foundations | Done |
| 1 | Auth, data model, consent | Done |
| 2 | Resume pipeline | Done (TF-IDF matching; sentence-transformers optional) |
| 3 | Assessments and activity | Done |
| 4 | Readiness predictor | Done on synthetic data; SHAP replaced by occlusion attribution |
| 5 | Mock interview | Done; server STT optional; facial analysis not built |
| 6 | Recommendation engine | Done (BKT); DKT not built |
| 7 | Aggregator and dashboards | Done |
| 8 | Evaluation and pilot harness | Done; human-rated interview and resume sets do not exist yet |
| 9 | Hardening and release | Mostly done; malware scanning and a hashed lock file are open (see [docs/SECURITY.md](docs/SECURITY.md)) |

Last verification (2026-10-27): GitHub Actions CI passing (ruff, mypy strict, 44 backend tests; frontend lint, typecheck, 4 tests, build). Docker Compose was not run locally (the Docker disk is on a full drive).
