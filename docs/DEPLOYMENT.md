# Deployment

## Frontend: Vercel (live)

Project `ai-placement-coach`, root directory `frontend`, deploys on every push to `main`.
Set `VITE_API_URL` (Production) to the Render API URL, then redeploy.

## Backend: Render

1. In Render choose **New → Blueprint** and pick this repo. `render.yaml` creates the API, Postgres 16 and Key Value (Redis).
2. Set `CORS_ORIGINS` to the Vercel URL (`https://ai-placement-coach-murex.vercel.app`), and `ADMIN_EMAIL` / `ADMIN_PASSWORD` for the first admin.
3. The image trains the bootstrap readiness model on synthetic data at build time. The API creates tables and seed data at startup.
4. `JOBS_INLINE=true` runs rescoring in the API process, so no paid worker is needed. To use the RQ worker, add a worker service running `python -m app.workers.run` and set `JOBS_INLINE=false`.

Free-tier caveats: the API sleeps when idle (the first request takes about 30-60 s), free Postgres expires, and uploaded files on local disk are lost on redeploy. Attach a Render disk at `/app/storage` or move storage to S3.

## Local

```
cp .env.example .env
docker compose up --build        # api :8000, web :5173, db, redis, worker
```

Without Docker, see the README.
