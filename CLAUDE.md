# AI Placement Coach: Persistent Context

AI-driven platform that evaluates an engineering student's placement readiness and gives personalized, continuously updated guidance. Four modules (Readiness Predictor, Resume & Skill-Gap Analyzer, Mock Interview Engine, Recommendation Engine) feed one Placement Readiness Score, a student dashboard and a coordinator dashboard. Full spec: `placement plan`. Work is delivered in phases (README has status).

## Working agreements (follow strictly)

- Work in **phases**. Finish one phase, run all tests, commit, then **stop and summarize** (what was built, how to run it, what is next, open questions). Wait for "continue".
- Before each phase, write a short plan (files to create or change, risks). Ask only about real blockers; otherwise choose sensible defaults and note them in `docs/DECISIONS.md`.
- Small commits with Conventional Commit messages (`feat:`, `fix:`, `test:`, `docs:`, `chore:`).
- Tests first or alongside. Never mark a task done with failing tests, lint errors or type errors.
- **Do not fabricate** data, metrics, benchmarks or citations. Synthetic or proxy data must be labeled as such in code, docs and UI. Report real measured results only.
- No secrets in git. Keep `.env.example` current. All config via environment variables.
- Type hints everywhere (Python), TypeScript strict mode (frontend). Keep functions small; document only where non-obvious.
- Keep `README.md` current: setup, run, test, architecture diagram, phase status.

## Tech stack (deviations go in DECISIONS.md)

| Layer | Choice |
|---|---|
| Backend API | Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2 + Alembic |
| Database | PostgreSQL 16 (JSONB for flexible artifacts) |
| Files | Local disk behind a storage interface (S3/MinIO later) |
| Jobs | Redis + RQ for heavy tasks |
| ML / NLP | scikit-learn, XGBoost/LightGBM, sentence-transformers, spaCy, pdfplumber, python-docx, SHAP |
| Speech | faster-whisper (STT), librosa (prosody) |
| Knowledge tracing | MVP: Bayesian Knowledge Tracing; stretch: PyTorch DKT |
| Frontend | React + TypeScript (Vite), Tailwind, React Query, Recharts, React Router |
| Auth | JWT (access + refresh); roles `student`, `coordinator`, `admin` |
| Quality | pytest, ruff, mypy, pre-commit; Vitest + Playwright |
| Infra | Docker Compose (api, worker, db, redis, web); GitHub Actions CI |

## Governance reminders

Consent per scope with versioning and revocation; PII pseudonymized before training/export; student view/export/delete-all; coordinators see cohort aggregates by default, individuals only with consent; audit log for sensitive reads. PII is never logged.
