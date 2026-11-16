/**
 * Hand-transcribed snapshot of docs/EVALUATION.md, which `scripts/evaluate.py` regenerates from
 * the live code. Kept in sync manually; update this file whenever that script is re-run.
 * Every section repeats its real data source so the Results page never implies a number is from
 * a real pilot when it is not.
 *
 * Section 1 (readiness predictor) now runs primarily on a REAL dataset: Krooz/Campus_Recruitment_CSV
 * (Hugging Face, CC0-1.0, public domain, 10,000 rows). It is real, anonymised student data, but
 * third-party and NOT SRM KTR or any institution of ours — no public SRM KTR placement dataset
 * could be found (see docs/DATA_PLAN.md). The synthetic generator's numbers are kept alongside it
 * as a labelled "_SYNTHETIC" comparison, exactly as docs/EVALUATION.md's §1b does.
 */

export const GENERATED_AT = "2026-11-16";

// ---------- Section 1: readiness predictor, REAL dataset (primary) ----------

export const REAL_DATASET_LABEL = "Krooz/Campus_Recruitment_CSV (Hugging Face, CC0-1.0, not SRM)";

export const MODEL_COMPARISON = [
  { model: "Logistic regression", cv_roc_auc: 0.8643 },
  { model: "Random forest", cv_roc_auc: 0.8634 },
  { model: "Hist. gradient boosting", cv_roc_auc: 0.8565 },
];

export const HOLDOUT = { accuracy: 0.7975, f1: 0.7532, roc_auc: 0.8759, brier: 0.1396 };

export const ABLATION = [
  { features: "Academics only", accuracy: 0.7915, roc_auc: 0.8499 },
  { features: "Full feature set", accuracy: 0.7975, roc_auc: 0.8759 },
];

export const CALIBRATION = [
  { bin: "0.0-0.2", n: 769, predicted: 0.094, observed: 0.09 },
  { bin: "0.2-0.4", n: 318, predicted: 0.289, observed: 0.308 },
  { bin: "0.4-0.6", n: 219, predicted: 0.498, observed: 0.466 },
  { bin: "0.6-0.8", n: 301, predicted: 0.705, observed: 0.698 },
  { bin: "0.8-1.0", n: 393, predicted: 0.864, observed: 0.916 },
];

// This real source has no demographic columns, so fairness cannot be checked on it.
export const FAIRNESS: { group: string; n: number; selection_rate: number; tpr: number; accuracy: number }[] = [];

// Five of our 13 features aren't recorded by this source and are held at a fixed constant
// (never imputed from unrelated columns), so they carry ~0 signal — this is why the
// ablation gap above is much smaller than on the synthetic generator below.
export const UNRECORDED_REAL_FEATURES = [
  "backlogs",
  "project_complexity",
  "problems_solved",
  "resume_score",
  "company_type_product",
];

// ---------- Section 1b: synthetic generator, kept as a labelled comparison ----------

export const MODEL_COMPARISON_SYNTHETIC = [
  { model: "Logistic regression", cv_roc_auc: 0.8913 },
  { model: "Random forest", cv_roc_auc: 0.8873 },
  { model: "Hist. gradient boosting", cv_roc_auc: 0.8731 },
];

export const HOLDOUT_SYNTHETIC = { accuracy: 0.7967, f1: 0.8135, roc_auc: 0.8926, brier: 0.1336 };

export const ABLATION_SYNTHETIC = [
  { features: "Academics only", accuracy: 0.6167, roc_auc: 0.6959 },
  { features: "Full feature set", accuracy: 0.7967, roc_auc: 0.8926 },
];

export const FAIRNESS_SYNTHETIC = [
  { group: "CSE", n: 156, selection_rate: 0.551, tpr: 0.783, accuracy: 0.782 },
  { group: "ECE", n: 102, selection_rate: 0.52, tpr: 0.83, accuracy: 0.824 },
  { group: "MECH", n: 42, selection_rate: 0.548, tpr: 0.85, accuracy: 0.786 },
  { group: "Female", n: 137, selection_rate: 0.46, tpr: 0.726, accuracy: 0.781 },
  { group: "Male", n: 163, selection_rate: 0.607, tpr: 0.87, accuracy: 0.81 },
];

// ---------- Sections 2-7: unchanged (still synthetic / fixture-based) ----------

export const RESUME_MATCH = [
  { embedder: "TF-IDF word+char (default)", precision: 1.0, recall: 1.0, tp: 22, fp: 0, fn: 0 },
  { embedder: "MiniLM sentence-transformer (opt-in)", precision: 1.0, recall: 1.0, tp: 22, fp: 0, fn: 0 },
];

export const KNOWLEDGE_TRACING = [
  { model: "DKT (LSTM, hidden 100)", auc: 0.7056 },
  { model: "BKT, per-skill fitted", auc: 0.7224 },
  { model: "BKT, default parameters", auc: 0.69 },
];

export const TRACKING_GAIN = [
  { company: "Product", policy: "Recommender", gap_closed: 0.4598 },
  { company: "Product", policy: "Random topic", gap_closed: 0.36 },
  { company: "Product", policy: "Fixed syllabus", gap_closed: 0.3769 },
  { company: "Service", policy: "Recommender", gap_closed: 0.5187 },
  { company: "Service", policy: "Random topic", gap_closed: 0.3872 },
  { company: "Service", policy: "Fixed syllabus", gap_closed: 0.4051 },
];

export const TARGETS = [
  { target: "~86% readiness accuracy", measured: "79.8% hold-out accuracy (real data)", comparable: false, why: "Real but third-party dataset (CC0, not SRM), not our own pilot" },
  { target: "~79% resume match precision", measured: "100% precision, 4 pairs", comparable: false, why: "4 author-written resume/JD pairs, not a human-annotated set" },
  { target: "r ≥ 0.75 interview vs human raters", measured: "Not yet measured", comparable: false, why: "No human-rated interview sample collected yet" },
  { target: "+25% skill-gap tracking gain", measured: "+27.7% to +34.0% (simulated)", comparable: false, why: "Simulator shares the recommender's own assumptions" },
  { target: "DKT AUC ~0.86 (ASSISTments, literature)", measured: "0.706 AUC (synthetic data)", comparable: false, why: "Different dataset; ASSISTments requires accepting its terms of use" },
];
