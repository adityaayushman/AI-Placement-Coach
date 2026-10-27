# Security checklist (Phase 9)

| Threat or control | Status | Where |
|---|---|---|
| Passwords hashed with a slow KDF | Done (scrypt, n=2^14) | `core/security.py` |
| JWT access (15 min) + refresh (7 days), token type checked | Done | `core/security.py`, `deps.py` |
| Role-based access on every route | Done, tested | `deps.py`, `tests/test_auth_rbac.py` |
| Public sign-up cannot create staff | Done, tested | `api/v1/auth.py` |
| Brute force on login and register | In-process limit, 20 POSTs/min/IP | `core/middleware.py` |
| CORS allowlist from env | Done | `main.py` |
| Security headers (nosniff, frame DENY, no-referrer) | Done | `core/middleware.py` |
| Input validation with bounds on every field | Done | `schemas/common.py` |
| Uploads: extension allowlist, size cap, magic bytes, DOCX zip-bomb guard, random server filenames, path-escape check | Done, tested | `api/v1/resumes.py`, `ml/resume/parsing.py`, `services/storage.py` |
| Malware scanning of uploads | **Not done.** Files are never executed or served back. Put ClamAV in front of storage before a public pilot | |
| PII kept out of logs | Logs carry request id, route and numeric ids only | `core/logging.py` |
| Consent enforced server-side | Done, tested (revoking blocks access) | `services/governance.py` |
| Coordinator re-identification | Groups under 3 suppressed; individual reads audited | `api/v1/coordinator.py` |
| Audit log for sensitive reads and admin actions | Done | `audit_log` |
| Secrets via env only, `.env` gitignored | Done | `.env.example` |
| Container runs as non-root | Done | `backend/Dockerfile` |
| Backups | `scripts/backup.sh` (pg_dump + files, 14-day retention). Schedule it with cron or a Render cron job | |
| Dependency lock with hashes | **Not done** (version ranges only). Generate a lock file before the pilot | |
| Load | `scripts/load_smoke.py`, 300 requests, 20 concurrent, non-ML reads, local single worker + SQLite: p50 185 ms, p95 334 ms, 0 errors (measured 2026-10-27) | |
