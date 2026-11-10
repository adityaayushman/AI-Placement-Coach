# Deployment

## Frontend: Vercel (live)

Project `ai-placement-coach`, root directory `frontend`, deploys on every push to `main`.
Set `VITE_API_URL` (Production) to the backend URL below, then redeploy.

## Backend: Hugging Face Spaces + Supabase (recommended — free, no payment details required)

Hugging Face's free Docker Spaces give 16 GB RAM (room for the ML models), and Supabase's free
Postgres tier needs no card. Together they replace Render without billing info on file.

**One-time setup:**

1. Create a free account at [huggingface.co](https://huggingface.co) (email only).
2. Create a write token: Settings → Access Tokens → New token → role **Write**.
3. In this GitHub repo: Settings → Secrets and variables → Actions:
   - Add **secret** `HF_TOKEN` = the token from step 2.
   - Add **variable** `HF_SPACE` = `<your-hf-username>/ai-placement-coach-api`.
4. Push to `main`, or run the **deploy-hf-space** workflow manually from the Actions tab. This
   creates the Space (Docker SDK, free CPU) on first run and pushes `backend/` into it.
5. In Supabase, open your project → **Project Settings → Database → Connect**, copy the URI
   (`postgresql://postgres.<ref>:<password>@...:5432/postgres`). Our config normalises
   `postgres://`/`postgresql://` automatically, so paste it as-is.
6. On the Space page → **Settings → Variables and secrets**, add:
   - `DATABASE_URL` — the Supabase URI from step 5
   - `SECRET_KEY` — any long random string
   - `CORS_ORIGINS` — the Vercel URL, e.g. `https://ai-placement-coach-murex.vercel.app`
   - `ADMIN_EMAIL` / `ADMIN_PASSWORD` — for the first admin account
7. The Space restarts automatically after secrets are saved. First boot trains the bootstrap
   readiness model on synthetic data and creates tables; takes 1-2 minutes.
8. Your API is live at `https://<username>-ai-placement-coach-api.hf.space`. Check
   `.../api/v1/health`.
9. In Vercel, set `VITE_API_URL` to that URL and redeploy the frontend.

No Redis is needed: the image's default `JOBS_INLINE=true` runs background jobs inside the API
process. Free Spaces sleep after inactivity and wake on the next request (10-30 s cold start).

## Backend: Render (alternative — free tier now asks for billing details on file)

1. In Render choose **New → Blueprint** and pick this repo. `render.yaml` creates the API,
   Postgres 16 and Key Value (Redis).
2. Set `CORS_ORIGINS` to the Vercel URL, and `ADMIN_EMAIL` / `ADMIN_PASSWORD` for the first admin.
3. The image trains the bootstrap readiness model on synthetic data at build time. The API
   creates tables and seed data at startup.
4. `JOBS_INLINE=true` runs rescoring in the API process, so no paid worker is needed. To use the
   RQ worker, add a worker service running `python -m app.workers.run` and set
   `JOBS_INLINE=false`.

Caveats: the API sleeps when idle (first request takes 30-60 s), free Postgres expires, and
uploaded files on local disk are lost on redeploy. Attach a Render disk at `/app/storage` or move
storage to S3.

## Local

```
cp .env.example .env
docker compose up --build        # api :8000, web :5173, db, redis, worker
```

Without Docker, see the README.
