# Data plan

| Stream | Table(s) | Consent scope | Status |
|---|---|---|---|
| Academic records | `student_profiles`, `academic_records` | core service | Form entry, student CSV import, staff import of an institutional ERP/LMS export |
| Resumes and certificates | `resumes`, `resume_analyses`, `certifications` | `resume` | Upload PDF/DOCX/TXT up to 5 MB, magic-byte checked |
| Coding and project activity | `coding_activities`, `projects` | core service | Form and CSV import |
| Target job descriptions | `job_descriptions` | n/a | Staff CRUD; seeded with 3 **illustrative samples** (generic names, not real postings) |
| Mock interview sessions | `interview_sessions`, `interview_answers` | `interview_recording` (audio), `face_analysis` (camera) | Text always allowed; audio stored only with consent; video never leaves the browser, only five summary numbers are stored |
| Interaction logs | `events` (append-only) | `analytics` | Not written without consent |

Coordinator individual access requires `coordinator_visibility`. Consents are append-only rows with version `2026-10`; the latest row per scope wins.

## Rights

- View and export: `GET /api/v1/me/export?format=json|csv`
- Delete: `DELETE /api/v1/me` hard-deletes every user-keyed row, interview answers, stored files and the account. An audit row records the deletion without PII.

## Development data provenance

| Data | Source | Licence | Label |
|---|---|---|---|
| Readiness training data | `app/ml/readiness/synthetic.py` (seeded generator) | own code | SYNTHETIC, shown in UI and docs |
| Resume/JD gap fixtures | `backend/tests/fixtures.py`, written by the authors | own | author-constructed, not human-annotated |
| Quiz and interview questions | `app/seed.py`, written by the authors | own | |
| Learning resources | links to public sites (CP-Algorithms, OSTEP, PostgreSQL docs, MDN and others) | linked, not copied | |

Not used yet (check the licence before use): Kaggle campus placement data, public resume and JD datasets, ASSISTments, RAVDESS. Pilot target: 200-300 students across 2-3 departments. Train on a pseudonymised export with `train_and_register(csv)`, then re-run `scripts/evaluate.py --csv`.
