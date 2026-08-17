"""Lightweight retrieval embeddings for Streamlit Cloud (TF-IDF, no GPU/torch)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _normalize(text: str) -> str:
    return " ".join((text or "").split())


@dataclass
class CorpusIndex:
    texts: List[str]
    vectorizer: TfidfVectorizer
    matrix: object


class TfidfRetriever:
    """Fit a TF-IDF index and rank documents by cosine similarity."""

    def __init__(self, ngram_range: Tuple[int, int] = (1, 2), max_features: int = 12000):
        self.ngram_range = ngram_range
        self.max_features = max_features

    def build(self, texts: Sequence[str]) -> CorpusIndex:
        cleaned = [_normalize(t) or " " for t in texts]
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=self.ngram_range,
            max_features=self.max_features,
            min_df=1,
            sublinear_tf=True,
        )
        matrix = vectorizer.fit_transform(cleaned)
        return CorpusIndex(texts=list(cleaned), vectorizer=vectorizer, matrix=matrix)

    def query(self, index: CorpusIndex, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        if not query.strip() or index.matrix.shape[0] == 0:
            return []
        query_vec = index.vectorizer.transform([_normalize(query)])
        scores = cosine_similarity(query_vec, index.matrix).flatten()
        if scores.size == 0:
            return []
        top_k = min(top_k, len(scores))
        order = np.argsort(scores)[::-1][:top_k]
        return [(int(i), float(scores[i])) for i in order if float(scores[i]) > 0]

    def pairwise_score(self, left: str, right: str) -> float:
        if not left.strip() or not right.strip():
            return 0.0
        overlap = _token_overlap(left, right)
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=self.ngram_range,
            min_df=1,
            sublinear_tf=True,
        )
        try:
            matrix = vectorizer.fit_transform([_normalize(left), _normalize(right)])
            tfidf = float(cosine_similarity(matrix[0], matrix[1])[0, 0])
        except ValueError:
            tfidf = 0.0
        return max(tfidf, 0.65 * tfidf + 0.35 * overlap)


def _token_overlap(left: str, right: str) -> float:
    a = set(left.lower().split())
    b = set(right.lower().split())
    if not a or not b:
        return 0.0
    return len(a & b) / max(len(a | b), 1)


def similarity_label(score: float) -> str:
    if score >= 0.45:
        return "Highly similar"
    if score >= 0.25:
        return "Moderately similar"
    if score >= 0.12:
        return "Weakly related"
    return "Dissimilar"


def recommendation_from_score(score: float) -> str:
    if score >= 0.45:
        return "Admit for presentation - strongly aligned with the case context."
    if score >= 0.25:
        return "Present with explanation - relevant, but not a close duplicate of existing materials."
    if score >= 0.12:
        return "Review before marking - only loosely connected to the pleaded facts."
    return "Likely irrelevant - similarity to the case context is too low."
