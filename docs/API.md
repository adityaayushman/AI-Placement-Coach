# API

Base path `/api/v1`. Interactive docs at `/docs`.

| Method | Path | Description |
|---|---|---|
| GET | /health | Liveness |
| GET | /ready | Readiness (DB + Redis), 503 if either is down |
