"""Compare automated interview scores with human ratings.

    cd backend && python ../scripts/compare_interview_ratings.py ratings.csv

ratings.csv columns: answer_id,human_overall (0-100). Reads automated scores from the database
configured by DATABASE_URL."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import pandas as pd  # noqa: E402
from scipy.stats import pearsonr, spearmanr  # noqa: E402

from app.db.models import InterviewAnswer  # noqa: E402
from app.db.session import get_sessionmaker  # noqa: E402


def main(path: str) -> None:
    human = pd.read_csv(path)
    with get_sessionmaker()() as db:
        auto = {a.id: a.scores.get("overall") for a in db.query(InterviewAnswer)
                .filter(InterviewAnswer.id.in_(human["answer_id"].tolist()))}
    human["auto_overall"] = human["answer_id"].map(auto)
    paired = human.dropna()
    if len(paired) < 10:
        sys.exit(f"Only {len(paired)} matched answers; need at least 10 for a meaningful r.")
    r, p = pearsonr(paired["human_overall"], paired["auto_overall"])
    rho, p2 = spearmanr(paired["human_overall"], paired["auto_overall"])
    print(f"n={len(paired)}  Pearson r={r:.3f} (p={p:.3g})  Spearman rho={rho:.3f} (p={p2:.3g})")


if __name__ == "__main__":
    main(sys.argv[1])
