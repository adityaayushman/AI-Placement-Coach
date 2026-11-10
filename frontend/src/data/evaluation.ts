/**
 * Hand-transcribed snapshot of docs/EVALUATION.md, which `scripts/evaluate.py` regenerates from
 * the live code. Kept in sync manually; update this file whenever that script is re-run.
 * Every section repeats its real data source so the Results page never implies a number is from
 * a real pilot when it is not.
 */

export const GENERATED_AT = "2026-10-27";

export const MODEL_COMPARISON = [
  { model: "Logistic regression", cv_roc_auc: 0.8913 },
  { model: "Random forest", cv_roc_auc: 0.8873 },
  { model: "Hist. gradient boosting", cv_roc_auc: 0.8731 },
];

export const HOLDOUT = { accuracy: 0.7967, f1: 0.8135, roc_auc: 0.8926, brier: 0.1336 };

export const ABLATION = [
  { features: "Academics only", accuracy: 0.6167, roc_auc: 0.6959 },
  { features: "Full feature set", accuracy: 0.7967, roc_auc: 0.8926 },
];

export const CALIBRATION = [
  { bin: "0.0-0.2", n: 74, predicted: 0.098, observed: 0.081 },
  { bin: "0.2-0.4", n: 47, predicted: 0.295, observed: 0.383 },
  { bin: "0.4-0.6", n: 41, predicted: 0.508, observed: 0.512 },
  { bin: "0.6-0.8", n: 46, predicted: 0.703, observed: 0.674 },
  { bin: "0.8-1.0", n: 92, predicted: 0.936, observed: 0.967 },
];

export const FAIRNESS = [
  { group: "CSE", n: 156, selection_rate: 0.551, tpr: 0.783, accuracy: 0.782 },
  { group: "ECE", n: 102, selection_rate: 0.52, tpr: 0.83, accuracy: 0.824 },
  { group: "MECH", n: 42, selection_rate: 0.548, tpr: 0.85, accuracy: 0.786 },
  { group: "Female", n: 137, selection_rate: 0.46, tpr: 0.726, accuracy: 0.781 },
  { group: "Male", n: 163, selection_rate: 0.607, tpr: 0.87, accuracy: 0.81 },
];

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
  { target: "~86% readiness accuracy", measured: "79.7% hold-out accuracy", comparable: false, why: "Measured on a synthetic generator, not real students" },
  { target: "~79% resume match precision", measured: "100% precision, 4 pairs", comparable: false, why: "4 author-written resume/JD pairs, not a human-annotated set" },
  { target: "r ≥ 0.75 interview vs human raters", measured: "Not yet measured", comparable: false, why: "No human-rated interview sample collected yet" },
  { target: "+25% skill-gap tracking gain", measured: "+27.7% to +34.0% (simulated)", comparable: false, why: "Simulator shares the recommender's own assumptions" },
  { target: "DKT AUC ~0.86 (ASSISTments, literature)", measured: "0.706 AUC (synthetic data)", comparable: false, why: "Different dataset; ASSISTments requires accepting its terms of use" },
];
