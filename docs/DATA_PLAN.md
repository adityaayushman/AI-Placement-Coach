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
| Readiness training data (default, live) | [Krooz/Campus_Recruitment_CSV](https://huggingface.co/datasets/Krooz/Campus_Recruitment_CSV), mapped by `scripts/prepare_real_dataset.py` to `backend/data/external/real_campus_placement.csv` | CC0-1.0 (public domain) | **REAL**, third-party; not SRM KTR or any institution of ours (see note below) |
| Readiness training data (fallback / dev) | `app/ml/readiness/synthetic.py` (seeded generator) | own code | SYNTHETIC, shown in UI and docs when active |
| Resume/JD gap fixtures | `backend/tests/fixtures.py`, written by the authors | own | author-constructed, not human-annotated |
| Quiz and interview questions | `app/seed.py`, written by the authors | own | |
| Learning resources | links to public sites (CP-Algorithms, OSTEP, PostgreSQL docs, MDN and others) | linked, not copied | |

### On the real dataset: why not SRM KTR

The user asked for the project's own campus (SRM KTR) placement dataset. A search (Kaggle,
Hugging Face, GitHub, Google) found **no public SRM KTR placement dataset** — only informal
Reddit figures and news-article placement statistics, not a row-level dataset. In its place we
use `Krooz/Campus_Recruitment_CSV`, a real (not synthetic), CC0-licensed, 10,000-row dataset of
anonymised student records from an unnamed "XYZ campus" per its own README. It is genuinely real
data, but it is **not SRM, and not our own pilot** — that distinction is carried in the
`data_source` string on every readiness score (`real:krooz-campus-recruitment-csv ... not SRM`)
and shown on the `/results` page, never presented as SRM or institutional data.

Five of our thirteen modelled features (`backlogs`, `project_complexity`, `problems_solved`,
`resume_score`, `company_type_product`) are not recorded by this source. Rather than guess them
from unrelated columns, `scripts/prepare_real_dataset.py` holds them at a fixed, documented
constant, so they carry zero statistical signal — an honest "unknown", not a fabricated value.

Controlled by `USE_REAL_BOOTSTRAP` (default **true** in the shipped Docker image, **false** in
tests and local dev unless set): when true and the bundled CSV is present, `ensure_model()`
trains the bootstrap model on it instead of the synthetic generator.

Not used yet (check the licence before use): public resume/JD datasets, ASSISTments, RAVDESS.
Pilot target: 200-300 real SRM KTR students across 2-3 departments, once the placement cell can
provide one. Train on that pseudonymised export with `train_and_register(csv)`, then re-run
`scripts/evaluate.py --csv <path>`.
