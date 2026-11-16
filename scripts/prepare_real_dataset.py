"""Map the real, third-party Krooz/Campus_Recruitment_CSV dataset onto our readiness schema.

Source: https://huggingface.co/datasets/Krooz/Campus_Recruitment_CSV (CC0-1.0, public domain).
Per its own README this is "placement data of students in a XYZ campus" — real, anonymised
student records, but **not SRM KTR or any institution of ours**. No public SRM KTR placement
dataset could be found (checked Kaggle, Hugging Face, GitHub); see docs/DATA_PLAN.md for the
search and for why this stand-in was chosen.

Column mapping to app.ml.readiness.model.FEATURES:
    cgpa              = CGPA                        (already 0-10)
    tenth_pct         = SSC_Marks
    twelfth_pct       = HSC_Marks
    internships       = Internships
    project_count     = Projects
    certifications    = Workshops/Certifications
    quiz_avg          = AptitudeTestScore            (already 0-100)
    interview_avg     = SoftSkillsRating * 20        (1-5 rating -> 0-100, a unit conversion)
    placed            = PlacementStatus == "Placed"

Columns this source does not record at all — backlogs, project_complexity, problems_solved,
resume_score, company_type_product — are held at a fixed neutral constant, never statistically
imputed from unrelated columns. A constant carries no variance, so it contributes ~0 to any
trained model; it is not fabricated signal, just an honest "unknown". ExtracurricularActivities
and PlacementTraining (Yes/No) have no matching column in our schema and are dropped rather than
force-mapped into something unrelated.

Usage:
    python scripts/prepare_real_dataset.py
Writes backend/data/external/real_campus_placement.csv (committed, and inside the backend's
Docker build context; CC0 permits redistribution, and the file carries no names or other
direct identifiers).
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "external" / "krooz_campus_recruitment"
OUT_PATH = ROOT / "backend" / "data" / "external" / "real_campus_placement.csv"

# Not recorded by this source; held constant and documented, never guessed from other columns.
NEUTRAL_CONSTANTS = {
    "backlogs": 0.0,
    "project_complexity": 2.0,  # midpoint of our 1-3 scale
    "problems_solved": 0.0,
    "resume_score": 0.0,
    "company_type_product": 0.0,
}


def load_raw() -> pd.DataFrame:
    frames = [pd.read_csv(RAW_DIR / f"{split}.csv") for split in ("train", "validation", "test")]
    return pd.concat(frames, ignore_index=True)


def map_to_schema(raw: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "cgpa": raw["CGPA"],
            "tenth_pct": raw["SSC_Marks"].astype(float),
            "twelfth_pct": raw["HSC_Marks"].astype(float),
            "internships": raw["Internships"],
            "project_count": raw["Projects"],
            "certifications": raw["Workshops/Certifications"],
            "quiz_avg": raw["AptitudeTestScore"].astype(float),
            "interview_avg": raw["SoftSkillsRating"] * 20,
            "placed": (raw["PlacementStatus"] == "Placed").astype(int),
        }
    )
    for col, value in NEUTRAL_CONSTANTS.items():
        out[col] = value
    return out


def main() -> None:
    mapped = map_to_schema(load_raw())
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    mapped.to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH} ({len(mapped)} rows, placed rate {mapped['placed'].mean():.3f})")


if __name__ == "__main__":
    main()
