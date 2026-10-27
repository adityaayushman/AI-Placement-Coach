"""Text embeddings behind one interface.

Default: TF-IDF (word 1-2 grams + char 3-5 grams) fitted on the texts being compared. This is a
lexical, not semantic, similarity. When USE_SENTENCE_TRANSFORMERS is set and the package is
installed, a BERT-family sentence-transformer is used instead (see docs/DECISIONS.md)."""

import logging
from functools import lru_cache
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from app.config import get_settings

log = logging.getLogger(__name__)


class Embedder(Protocol):
    name: str

    def similarity(self, queries: list[str], targets: list[str]) -> NDArray[np.float64]: ...


class TfidfEmbedder:
    name = "tfidf-word+char"

    def similarity(self, queries: list[str], targets: list[str]) -> NDArray[np.float64]:
        from scipy.sparse import hstack
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        corpus = [t or " " for t in queries + targets]
        word = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
        char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
        try:
            mat = hstack([word.fit_transform(corpus), char.fit_transform(corpus)]).tocsr()
        except ValueError:  # empty vocabulary
            return np.zeros((len(queries), len(targets)))
        q, t = mat[: len(queries)], mat[len(queries) :]
        return np.asarray(cosine_similarity(q, t), dtype=np.float64)


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        self.name = f"st:{model_name}"

    def similarity(self, queries: list[str], targets: list[str]) -> NDArray[np.float64]:
        q = self.model.encode(queries, normalize_embeddings=True)
        t = self.model.encode(targets, normalize_embeddings=True)
        return np.asarray(q @ t.T, dtype=np.float64)


@lru_cache
def get_embedder() -> Embedder:
    if get_settings().use_sentence_transformers:
        try:
            return SentenceTransformerEmbedder()
        except ImportError:
            log.warning("sentence-transformers not installed; falling back to TF-IDF")
    return TfidfEmbedder()
