# API

Base path `/api/v1`. Interactive docs at `/docs`. Auth: `Authorization: Bearer <access token>`.

| Area | Endpoints |
|---|---|
| Health | `GET /health`, `GET /ready` (DB + Redis, 503 if down), `GET /metrics` (count and p95 per route) |
| Auth | `POST /auth/register` (student only), `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me` |
| Profile and activity (student) | `GET/PUT /me/profile`; `GET/POST/DELETE /me/academics`, `/me/coding`, `/me/projects`, `/me/certifications`; `POST /me/coding/import`, `POST /me/academics/import` (CSV) |
| Consent and rights | `GET/PUT /consents`, `GET /me/export?format=json\|csv`, `DELETE /me` |
| Resume | `POST /resumes` (multipart `file`, optional `jd_id`), `POST /resumes/{id}/analyze?jd_id=`, `GET /resumes`, `GET /resumes/analyses/latest` |
| Job descriptions | `GET /jobs`; staff: `POST /jobs`, `DELETE /jobs/{id}` |
| Practice | `GET /assessments`, `GET /assessments/{id}`, `POST /assessments/{id}/attempts`, `GET /me/attempts`, `GET /me/mastery` |
| Recommendations | `GET /me/recommendations`, `PATCH /me/recommendations/{id}` with `accepted`, `ignored` or `completed` |
| Interview | `GET /interviews/stt`, `POST /interviews/sessions`, `POST /interviews/sessions/{id}/answers` (multipart `question_id`, `transcript`, optional WAV `audio`, optional `face_metrics` JSON), `GET /interviews/sessions/{id}/answers` |
| Readiness | `GET /me/readiness` (latest, history, change), `POST /me/readiness/refresh` |
| Coordinator (staff) | `GET /coordinator/cohort?company_type=`, `GET /coordinator/students?at_risk=`, `GET /coordinator/students.csv`, `GET/POST /announcements` |
| Admin | `POST /admin/users`, `GET /admin/audit`, `GET /admin/models`, `POST /admin/models/retrain`, `POST /admin/questions`, `POST /admin/resources`; staff: `POST /admin/academics/import` (institutional CSV: email,term,gpa,backlogs) |
