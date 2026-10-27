"""SYNTHETIC cohort generator. Not real student data.

Students get two latent traits: aptitude (drives academics and partly practice) and effort
(drives practice: coding, projects, quizzes, interviews). The placement label depends on both
plus noise. Because the generator *assumes* practice matters more than marks, any ablation run on
this data reflects that assumption and is not evidence about real students."""

import numpy as np
import pandas as pd

DEPARTMENTS = ["CSE", "ECE", "MECH"]
GENDERS = ["female", "male"]
SYNTHETIC_LABEL = "synthetic-v1"


def generate(n: int = 1500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    aptitude = rng.normal(size=n)
    effort = rng.normal(size=n)
    dept = rng.choice(DEPARTMENTS, size=n, p=[0.5, 0.3, 0.2])
    df = pd.DataFrame(
        {
            "department": dept,
            "gender": rng.choice(GENDERS, size=n),
            "company_type_product": rng.integers(0, 2, size=n),
            "cgpa": np.clip(7.2 + 0.9 * aptitude + rng.normal(0, 0.5, n), 4, 10).round(2),
            "backlogs": rng.poisson(np.clip(0.8 - 0.6 * aptitude, 0.05, None)),
            "tenth_pct": np.clip(80 + 7 * aptitude + rng.normal(0, 6, n), 40, 100).round(1),
            "twelfth_pct": np.clip(76 + 8 * aptitude + rng.normal(0, 7, n), 40, 100).round(1),
            "internships": rng.poisson(np.clip(0.6 + 0.5 * effort, 0.05, None)),
            "project_count": rng.poisson(np.clip(2 + 1.2 * effort, 0.1, None)),
            "project_complexity": np.clip(1.5 + 0.5 * effort + rng.normal(0, 0.4, n), 1, 3).round(
                2
            ),
            "certifications": rng.poisson(np.clip(1 + 0.8 * effort, 0.05, None)),
            "problems_solved": np.clip(
                rng.lognormal(4.5 + 0.7 * effort + 0.3 * aptitude, 0.6, n), 0, 3000
            ).round(),
            "quiz_avg": np.clip(55 + 10 * effort + 8 * aptitude + rng.normal(0, 10, n), 0, 100),
            "resume_score": np.clip(60 + 9 * effort + rng.normal(0, 10, n), 0, 100),
            "interview_avg": np.clip(55 + 8 * effort + 5 * aptitude + rng.normal(0, 12, n), 0, 100),
        }
    )
    # ECE/MECH students apply to fewer software roles in this toy world.
    dept_shift = np.select([dept == "CSE", dept == "ECE"], [0.3, 0.0], -0.3)
    logit = (
        0.6 * aptitude + 1.3 * effort + dept_shift - 0.25 * df["backlogs"] + rng.normal(0, 0.9, n)
    )
    df["placed"] = (logit > np.quantile(logit, 0.45)).astype(int)
    # Realistic missingness: not everyone has done quizzes or mock interviews yet.
    for col, frac in [("quiz_avg", 0.2), ("interview_avg", 0.35), ("resume_score", 0.1)]:
        df.loc[rng.random(n) < frac, col] = np.nan
    return df
