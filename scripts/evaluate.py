"""Regenerate docs/EVALUATION.md from measured results.

    cd backend && python ../scripts/evaluate.py [--csv path/to/real_pseudonymised.csv]

Every table states its data source. Synthetic results describe the generator, not students."""

import argparse
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("MODEL_DIR", str(ROOT / "backend" / "models-eval"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from app.ml.knowledge import bkt  # noqa: E402
from app.ml.readiness import model as readiness  # noqa: E402
from app.ml.readiness.synthetic import SYNTHETIC_LABEL, generate  # noqa: E402
from app.ml.resume.analyzer import analyze  # noqa: E402
from app.seed import SAMPLE_JDS  # noqa: E402

sys.path.insert(0, str(ROOT / "backend"))
from tests.fixtures import GAP_CASES  # noqa: E402


def table(rows: list[dict[str, object]], cols: list[str]) -> str:
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join("" if r.get(c) is None else str(r.get(c)) for c in cols) + " |"
            for r in rows]
    return "\n".join(out)


def readiness_section(csv: str | None) -> str:
    if csv:
        df, source = pd.read_csv(csv), f"CSV `{Path(csv).name}`"
    else:
        df, source = generate(1500), f"**SYNTHETIC** generator `{SYNTHETIC_LABEL}` (n=1500)"
    rep = readiness.train(df, source)["report"]
    cv = [{"model": k, "cv_roc_auc_mean": v["mean"], "std": v["std"]}
          for k, v in rep["cv_roc_auc"].items()]
    abl = rep["ablation"]
    ablation = [
        {"features": "academics only (CGPA, backlogs, 10th, 12th)",
         **abl["academics_only"]["holdout"]},
        {"features": "full feature set", **abl["full"]["holdout"]},
    ]
    fair = []
    for attr, rows in rep["fairness"].items():
        fair += [{"attribute": attr, **r} for r in rows]
    caveat = (
        "> These numbers are measured on synthetic data. The generator assumes practice "
        "features matter more than marks, so the ablation result is built in and is **not "
        "evidence** about real students. Re-run with `--csv` on a pseudonymised pilot export.\n"
        if not csv else ""
    )
    return f"""## 1. Placement readiness predictor

Data: {source}. Train/test split 80/20 stratified, seed 42; positive rate {rep['positive_rate']}.
Data hash `{rep['data_hash'][:16]}`.

{caveat}
### Model selection (5-fold stratified CV on the training split)

{table(cv, ["model", "cv_roc_auc_mean", "std"])}

Selected: **{rep['selected']}**, calibrated with {rep['calibration']}.

### Hold-out performance

{table([rep['holdout']], ["accuracy", "f1", "roc_auc", "brier"])}

### Ablation: academics-only vs full features (same model family, hold-out)

{table(ablation, ["features", "accuracy", "f1", "roc_auc", "brier"])}

### Calibration (hold-out reliability table)

{table(rep['calibration_table'], ["bin", "n", "mean_predicted", "observed_rate"])}

### Fairness slices (hold-out, threshold 0.5)

{table(fair, ["attribute", "group", "n", "selection_rate", "true_positive_rate", "accuracy"])}

Explanations: occlusion attribution (feature reset to training median), not SHAP; SHAP is not
installed in this environment.
"""


def skill_gap_section() -> str:
    tp = fp = fn = 0
    rows = []
    for i, (resume, jd_idx, expected) in enumerate(GAP_CASES):
        got = {g["skill"] for g in analyze(resume, SAMPLE_JDS[jd_idx])["skill_gaps"]}
        tp += len(got & expected)
        fp += len(got - expected)
        fn += len(expected - got)
        rows.append({"case": i + 1, "jd": SAMPLE_JDS[jd_idx]["role"], "expected": len(expected),
                     "detected": len(got), "correct": len(got & expected)})
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    return f"""## 2. Resume skill-gap detection

Data: {len(GAP_CASES)} **author-constructed** resume/JD pairs in `backend/tests/fixtures.py`, with
gap labels defined by construction. This is a regression check, not a human-annotated
evaluation; it is also the set the semantic threshold was tuned on, so it overstates accuracy.

{table(rows, ["case", "jd", "expected", "detected", "correct"])}

Micro precision **{precision:.2f}**, recall **{recall:.2f}** (TP={tp}, FP={fp}, FN={fn}).

Rank correlation with human judgement: **not measured** (no human-annotated pairs yet).
Embedder: TF-IDF word+char n-grams (lexical); sentence-transformers is optional and was not used.
"""


def bkt_section() -> str:
    from sklearn.metrics import roc_auc_score

    rng = np.random.default_rng(0)
    p_true = bkt.DEFAULT
    y, scores = [], []
    for _ in range(300):
        known = rng.random() < p_true.p_init
        est = p_true.p_init
        for _ in range(12):
            correct = rng.random() < ((1 - p_true.p_slip) if known else p_true.p_guess)
            scores.append(bkt.predict_correct(est))
            y.append(int(correct))
            est = bkt.update(est, bool(correct))
            known = known or rng.random() < p_true.p_learn
    auc = roc_auc_score(y, scores)
    return f"""## 3. Knowledge tracing (BKT)

Data: **SYNTHETIC** sequences simulated from the same BKT parameters the model uses (300
students x 12 attempts). Next-attempt ROC-AUC: **{auc:.3f}**. Because the simulator and model share
parameters this only checks the implementation; it says nothing about real learners.
ASSISTments validation and DKT: **not run** (dataset not downloaded; PyTorch not installed).
"""


INTERVIEW = """## 4. Mock-interview scoring

Automated vs human ratings: **not measured**. No human-rated answers exist yet.
`scripts/compare_interview_ratings.py ratings.csv` computes Pearson and Spearman r once raters
score a sample (CSV columns: `answer_id,human_overall`). Unit tests only check that clearly good
answers outscore clearly poor ones.
"""

TARGETS = """## 5. Reference lines from the literature (not our results)

These come from the project brief and have not been re-verified here: readiness accuracy in the
high-70s to mid-80s %, resume-role match near 79%, interview automated-human r >= 0.75, DKT AUC
about 0.86 on ASSISTments. None of our numbers above are comparable to these until we evaluate on
real pilot data.
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="pseudonymised CSV with readiness FEATURES + placed")
    args = ap.parse_args()
    stamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    doc = "\n".join([
        "# Evaluation\n",
        f"Generated by `scripts/evaluate.py` on {stamp}. Do not edit by hand.\n",
        readiness_section(args.csv), skill_gap_section(), bkt_section(), INTERVIEW, TARGETS,
    ])
    (ROOT / "docs" / "EVALUATION.md").write_text(doc, encoding="utf-8")
    print("wrote docs/EVALUATION.md")


if __name__ == "__main__":
    main()
