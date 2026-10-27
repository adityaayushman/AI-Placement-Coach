# Decisions

Format: date, decision, reason. Newest last.

## Phase 0 (2026-10-27)

1. **Repo root is the existing `placement coach` folder**, not a nested `ai-placement-coach/`. The folder already exists and holds the spec file; nesting adds no value.
2. **Local Python is 3.12, containers and CI use 3.11.** `requires-python = ">=3.11"`; code must not use 3.12-only features. CI is the source of truth.
3. **Tailwind v3** (PostCSS) rather than v4, for stable, widely documented config.
4. **Dependencies are split by phase.** Phase 0 `pyproject.toml` has only API/worker/test tooling. Heavy ML deps (torch, sentence-transformers, spaCy, faster-whisper) are added in the phase that needs them, to keep images and CI fast. Pinned lockfile/hashes arrive with the ML phases (reproducibility requirement).
5. **Worker is a stub in Phase 0**: RQ worker process starts and connects to Redis; no tasks yet.
6. **`/api/v1/health` is liveness only; `/api/v1/ready`** checks DB and Redis. Metrics endpoint comes with observability work in Phase 9 (request IDs and structured logs are in from Phase 0).
7. **No MongoDB.** PostgreSQL + JSONB only, per spec.
8. **Playwright e2e is deferred** to the first phase with a real user flow (Phase 1). Vitest is set up now.
9. **No database migrations in Phase 0.** Alembic is wired in Phase 1 together with the data model.
10. **Deployment targets: frontend on Vercel, backend on Render** (user instruction). `frontend/vercel.json` (SPA rewrite) and `render.yaml` (API web service, RQ worker, Postgres 16, Key Value/Redis) are provided but nothing is deployed. Docker Compose is for local development only. Consequences:
    - `VITE_API_URL` is a Vercel build-time env var pointing at the Render API URL; `CORS_ORIGINS` on Render must list the Vercel URL(s).
    - Render's `DATABASE_URL` is `postgres://`; Phase 1 must normalize it to `postgresql+psycopg://` in config.
    - Render free web tier sleeps and free Postgres expires: fine for a demo, not for the pilot. Uploaded files on local disk are lost on redeploy unless a Render persistent disk or S3/MinIO is used (decide in Phase 2). Heavy ML deps (Phase 4+) will need a larger Render instance.
    - The local `web` service in Compose stays as a production-like check of the frontend build.
