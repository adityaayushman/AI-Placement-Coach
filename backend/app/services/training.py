"""Train the readiness model from a CSV (real, pseudonymised export) or the synthetic generator,
and record it in `model_versions`."""

import logging

import pandas as pd

from app.config import get_settings
from app.db.models import ModelVersion
from app.db.session import get_sessionmaker
from app.ml.readiness import model as readiness
from app.ml.readiness.synthetic import SYNTHETIC_LABEL, generate

log = logging.getLogger(__name__)


def train_and_register(csv_path: str | None = None) -> str:
    if csv_path:
        df = pd.read_csv(csv_path)
        missing = {*readiness.FEATURES, "placed"} - set(df.columns)
        if missing:
            raise ValueError(f"CSV is missing columns: {sorted(missing)}")
        source = f"csv:{csv_path}"
    else:
        df, source = generate(get_settings().synthetic_rows), SYNTHETIC_LABEL
    result = readiness.train(df, source)
    version = readiness.save(result["artifact"])
    report = result["report"]
    with get_sessionmaker()() as db:
        for mv in db.query(ModelVersion).filter(ModelVersion.name == "readiness"):
            mv.is_active = False
        db.add(
            ModelVersion(
                name="readiness",
                version=version,
                data_hash=report["data_hash"],
                metrics={"holdout": report["holdout"], "source": source},
                is_active=True,
            )
        )
        db.commit()
    log.info("trained %s on %s", version, source)
    return version
