"""Deep Knowledge Tracing (Piech et al., 2015): an LSTM over (skill, correct) interactions that
predicts, for every skill, the probability the next answer on it is correct.

Requires PyTorch (pip install ".[ml-heavy]"). Trained here on SYNTHETIC sequences from
`simulate_sequences`; ASSISTments was not downloaded (licence terms must be accepted by a person).
Mastery estimates are served only when USE_DKT is set and a trained model exists."""

import itertools
import logging
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from app.config import get_settings
from app.ml.knowledge import bkt

log = logging.getLogger(__name__)
SEED = 13
Seq = list[tuple[int, bool]]  # (skill index, correct)


# ---------- SYNTHETIC data ----------


def simulate_sequences(
    n_skills: int = 10, learners: int = 800, length: int = 40, seed: int = SEED
) -> list[Seq]:
    """Learners practise random skills; skills have their own slip/guess/learn rates and each
    skill after the first depends on the previous one (knowing it doubles the learning rate).
    These cross-skill effects are what DKT can pick up and single-skill BKT cannot."""
    rng = np.random.default_rng(seed)
    learn = rng.uniform(0.05, 0.25, n_skills)
    slip = rng.uniform(0.05, 0.2, n_skills)
    guess = rng.uniform(0.1, 0.35, n_skills)
    seqs = []
    for _ in range(learners):
        known = rng.random(n_skills) < 0.2
        seq: Seq = []
        for _ in range(length):
            s = int(rng.integers(n_skills))
            p = (1 - slip[s]) if known[s] else guess[s]
            seq.append((s, bool(rng.random() < p)))
            boost = 2.0 if s > 0 and known[s - 1] else 1.0
            if not known[s] and rng.random() < min(1.0, learn[s] * boost):
                known[s] = True
        seqs.append(seq)
    return seqs


# ---------- BKT baseline with per-skill parameters fitted by grid search ----------


def _bkt_preds(seqs: list[Seq], params: dict[int, bkt.BKTParams]) -> tuple[list[int], list[float]]:
    y, p = [], []
    for seq in seqs:
        state: dict[int, float] = {}
        for s, c in seq:
            prm = params.get(s, bkt.DEFAULT)
            k = state.get(s, prm.p_init)
            p.append(bkt.predict_correct(k, prm))
            y.append(int(c))
            state[s] = bkt.update(k, c, prm)
    return y, p


def fit_bkt(seqs: list[Seq], n_skills: int) -> dict[int, bkt.BKTParams]:
    from sklearn.metrics import log_loss

    grid = list(
        itertools.product([0.1, 0.3, 0.5], [0.05, 0.15, 0.3], [0.05, 0.15], [0.1, 0.25, 0.4])
    )
    fitted = {}
    for s in range(n_skills):
        only = [[(sk, c) for sk, c in q if sk == s] for q in seqs]
        best, best_loss = bkt.DEFAULT, float("inf")
        for pi, pl, ps, pg in grid:
            prm = bkt.BKTParams(pi, pl, ps, pg)
            y, p = _bkt_preds(only, {s: prm})
            if len(set(y)) < 2:
                continue
            loss = log_loss(y, np.clip(p, 1e-6, 1 - 1e-6))
            if loss < best_loss:
                best, best_loss = prm, loss
        fitted[s] = best
    return fitted


# ---------- DKT ----------


def _require_torch() -> Any:
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("PyTorch is not installed; pip install '.[ml-heavy]'") from exc
    return torch


def _encode(seqs: list[Seq], n_skills: int) -> tuple[Any, Any, Any, Any]:
    """Inputs one-hot over 2*n_skills; targets are next-step (skill, correct) with a mask."""
    torch = _require_torch()
    length = max(len(s) for s in seqs) - 1
    x = torch.zeros(len(seqs), length, 2 * n_skills)
    nxt_skill = torch.zeros(len(seqs), length, dtype=torch.long)
    nxt_correct = torch.zeros(len(seqs), length)
    mask = torch.zeros(len(seqs), length)
    for i, seq in enumerate(seqs):
        for t in range(len(seq) - 1):
            s, c = seq[t]
            x[i, t, s + (n_skills if c else 0)] = 1
            nxt_skill[i, t], nxt_correct[i, t] = seq[t + 1][0], float(seq[t + 1][1])
            mask[i, t] = 1
    return x, nxt_skill, nxt_correct, mask


def build_model(n_skills: int, hidden: int = 100) -> Any:
    torch = _require_torch()

    class DKT(torch.nn.Module):  # type: ignore[misc,name-defined]
        def __init__(self) -> None:
            super().__init__()
            self.lstm = torch.nn.LSTM(2 * n_skills, hidden, batch_first=True)
            self.out = torch.nn.Linear(hidden, n_skills)

        def forward(self, x: Any) -> Any:
            h, _ = self.lstm(x)
            return torch.sigmoid(self.out(h))

    return DKT()


# Hidden size, learning rate and epochs chosen on a validation split (2026-10-27 sweep).
def train_dkt(seqs: list[Seq], n_skills: int, epochs: int = 15) -> Any:
    torch = _require_torch()
    torch.manual_seed(SEED)
    model = build_model(n_skills)
    opt = torch.optim.Adam(model.parameters(), lr=0.003)
    x, ns, nc, mask = _encode(seqs, n_skills)
    for _ in range(epochs):
        for idx in torch.randperm(len(seqs)).split(64):
            pred = model(x[idx]).gather(2, ns[idx].unsqueeze(-1)).squeeze(-1)
            loss = torch.nn.functional.binary_cross_entropy(pred, nc[idx], weight=mask[idx])
            opt.zero_grad()
            loss.backward()
            opt.step()
    model.eval()
    return model


def dkt_preds(model: Any, seqs: list[Seq], n_skills: int) -> tuple[list[int], list[float]]:
    torch = _require_torch()
    x, ns, nc, mask = _encode(seqs, n_skills)
    with torch.no_grad():
        pred = model(x).gather(2, ns.unsqueeze(-1)).squeeze(-1)
    keep = mask.bool()
    return nc[keep].int().tolist(), pred[keep].tolist()


def compare(n_skills: int = 10, learners: int = 2000, epochs: int = 15) -> dict[str, Any]:
    """Held-out next-answer ROC-AUC: DKT vs per-skill fitted BKT vs default BKT."""
    from sklearn.metrics import roc_auc_score

    seqs = simulate_sequences(n_skills, learners)
    split = int(0.8 * len(seqs))
    train, test = seqs[:split], seqs[split:]
    fitted = fit_bkt(train, n_skills)

    def bkt_auc(params: dict[int, bkt.BKTParams]) -> float:
        # Same targets as DKT: every answer except each sequence's first.
        ys, ps = [], []
        for seq in test:
            y, p = _bkt_preds([seq], params)
            ys += y[1:]
            ps += p[1:]
        return float(roc_auc_score(ys, ps))

    model = train_dkt(train, n_skills, epochs)
    y, p = dkt_preds(model, test, n_skills)
    return {
        "learners_train": len(train),
        "learners_test": len(test),
        "skills": n_skills,
        "auc_dkt": round(float(roc_auc_score(y, p)), 4),
        "auc_bkt_fitted": round(bkt_auc(fitted), 4),
        "auc_bkt_default": round(bkt_auc({}), 4),
    }


# ---------- optional serving ----------


def _path() -> Path:
    return Path(get_settings().model_dir) / "dkt" / "model.pt"


def save(model: Any, skills: list[str]) -> None:
    torch = _require_torch()
    _path().parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state": model.state_dict(), "skills": skills}, _path())


def mastery_from_history(history: list[tuple[str, bool]]) -> dict[str, float] | None:
    """Predicted P(correct next) per skill after a student's answer history, or None when DKT is
    disabled, PyTorch is missing, or no trained model exists."""
    if not get_settings().use_dkt or not _path().exists():
        return None
    try:
        torch = _require_torch()
    except RuntimeError:
        return None
    blob = torch.load(_path(), weights_only=True)
    skills: list[str] = blob["skills"]
    model = build_model(len(skills))
    model.load_state_dict(blob["state"])
    model.eval()
    idx = {s: i for i, s in enumerate(skills)}
    seq = [(idx[s], c) for s, c in history if s in idx]
    if not seq:
        return None
    x = torch.zeros(1, len(seq), 2 * len(skills))
    for t, (s, c) in enumerate(seq):
        x[0, t, s + (len(skills) if c else 0)] = 1
    with torch.no_grad():
        probs: NDArray[np.float64] = model(x)[0, -1].numpy()
    return {s: round(float(probs[i]), 4) for s, i in idx.items()}
