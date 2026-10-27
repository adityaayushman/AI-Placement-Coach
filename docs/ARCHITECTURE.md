# Architecture

```
Browser (React SPA on Vercel)
  │  JWT bearer, JSON / multipart
  ▼
FastAPI (Render web service): request id, JSON logs, security headers, auth rate limit, metrics
  ├─ api/v1/*         auth, /me (profile and activity), privacy, resumes + jobs, learning,
  │                   interviews, readiness, coordinator, admin, health
  ├─ services/        governance (consent, audit, events), storage, knowledge, aggregator,
  │                   rescoring, training
  ├─ ml/resume        parsing → sections → skills → ATS rules → JD match → ranked gaps
  ├─ ml/readiness     synthetic generator, CV model selection, calibration, registry, attribution
  ├─ ml/interview     prosody (numpy), optional STT, content / communication / delivery scoring
  ├─ ml/knowledge     BKT update, recommender (gap × weight × prerequisite readiness)
  └─ ml/embeddings    TF-IDF default, sentence-transformers optional
        │                         │
        ▼                         ▼
  PostgreSQL (JSONB)        Redis + RQ worker: workers/tasks.rescore_student, retrain_readiness
```

## Continuous-improvement loop

Any write that changes a student's evidence (profile, coding log, project, certification, resume, quiz attempt, interview answer) calls `request_rescore(user_id)`. The worker, or the API itself when `JOBS_INLINE=true`, builds the feature vector, runs the active readiness model, blends five components with per-company-type weights, and appends a `readiness_scores` row with `model_version`, weights and attributions. Quiz and interview answers also update BKT mastery and refresh recommendations. Accepting, completing or ignoring a recommendation feeds back into the ranking.

## Readiness score

`score = Σ wᵢ · componentᵢ` over components that have data, with weights renormalised. Components: predictor probability × 100; resume (0.6 × ATS + 40 × keyword coverage); weighted BKT mastery; interview average; consistency (active days in the last 28). Weights live in `services/aggregator.py` and are stored with each score.

## Data separation

PII (email, name) lives on `users`. Everything else hangs off `user_id`, and exports for modelling use `student_profiles.pseudonym_id`. Audit rows have no foreign key, so they survive account deletion.
