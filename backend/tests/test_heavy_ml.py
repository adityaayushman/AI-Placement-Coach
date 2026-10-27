"""Tests for the optional heavy backends. Skipped when PyTorch / sentence-transformers are absent
(the default CI install), run when `.[ml-heavy]` is installed."""

import pytest

from app.ml.knowledge import dkt


def test_synthetic_sequences_are_reproducible() -> None:
    a = dkt.simulate_sequences(n_skills=4, learners=20, length=10)
    b = dkt.simulate_sequences(n_skills=4, learners=20, length=10)
    assert a == b
    assert all(len(s) == 10 for s in a)


def test_fitted_bkt_returns_params_per_skill() -> None:
    seqs = dkt.simulate_sequences(n_skills=3, learners=60, length=15)
    fitted = dkt.fit_bkt(seqs, 3)
    assert set(fitted) == {0, 1, 2}


def test_dkt_trains_and_learns_signal() -> None:
    # Checks the model learns, not that it wins: on this synthetic data fitted BKT does better
    # (see docs/EVALUATION.md).
    pytest.importorskip("torch")
    result = dkt.compare(n_skills=5, learners=200, epochs=8)
    assert 0.6 < result["auc_dkt"] <= 1
    assert {"auc_bkt_fitted", "auc_bkt_default"} <= set(result)


def test_dkt_serving_is_off_by_default() -> None:
    assert dkt.mastery_from_history([("algorithms", True)]) is None


def test_sentence_transformer_embedder_ranks_related_text_higher() -> None:
    pytest.importorskip("sentence_transformers")
    from app.ml.embeddings import SentenceTransformerEmbedder

    try:
        emb = SentenceTransformerEmbedder()
    except OSError as exc:  # model weights not downloadable in this environment
        pytest.skip(f"model unavailable: {exc}")
    sims = emb.similarity(
        ["Built REST APIs with FastAPI and PostgreSQL"],
        ["backend web services and databases", "watercolour painting and poetry"],
    )
    assert sims[0, 0] > sims[0, 1]
