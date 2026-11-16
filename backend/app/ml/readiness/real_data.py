"""Loads the bundled real, third-party campus placement dataset as an alternative bootstrap
source to the synthetic generator.

This is REAL (anonymised) student data, not generated — but it is not ours. Its own README says
only "placement data of students in a XYZ campus"; no public SRM KTR placement dataset could be
found (Kaggle, Hugging Face and GitHub were checked). See docs/DATA_PLAN.md for the search and
`scripts/prepare_real_dataset.py` for the column mapping and its documented limitations (five of
our thirteen features are not recorded by this source and are held at a fixed constant, never
fabricated from unrelated columns).

Source: https://huggingface.co/datasets/Krooz/Campus_Recruitment_CSV (CC0-1.0, public domain).
"""

from pathlib import Path

import pandas as pd

REAL_DATASET_LABEL = "real:krooz-campus-recruitment-csv (CC0-1.0, third-party, not SRM)"
DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "external" / "real_campus_placement.csv"


def available() -> bool:
    return DATA_PATH.exists()


def load() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Real dataset not bundled at {DATA_PATH}; run scripts/prepare_real_dataset.py"
        )
    return pd.read_csv(DATA_PATH)
