"""Small, local retrieval helpers. No API key, no vector database."""

import re

from rank_bm25 import BM25Okapi

STOPWORDS = set("""a an and are as at be by can do does for from has have how i if in is it its
of on or our the their there this to was we what when where which who will with you your""".split())


def tokenize(text: str, drop_stopwords: bool = False) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in STOPWORDS] if drop_stopwords else words


class BM25Index:
    """BM25 over a list of text chunks. search() returns (score, chunk) pairs, best first."""

    def __init__(self, chunks: list[str], drop_stopwords: bool = True):
        self.chunks = chunks
        self.drop_stopwords = drop_stopwords
        self.bm25 = BM25Okapi([tokenize(c, drop_stopwords) for c in chunks])

    def search(self, query: str, k: int = 3) -> list[tuple[float, str]]:
        scores = self.bm25.get_scores(tokenize(query, self.drop_stopwords))
        order = sorted(range(len(self.chunks)), key=lambda i: scores[i], reverse=True)
        return [(float(scores[i]), self.chunks[i]) for i in order[:k]]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def rank_fusion(*rankings: list[int], k: int = 60) -> list[int]:
    """Reciprocal rank fusion: merge several best-first lists of ids into one."""
    score: dict[int, float] = {}
    for ranking in rankings:
        for pos, item in enumerate(ranking):
            score[item] = score.get(item, 0.0) + 1.0 / (k + pos + 1)
    return sorted(score, key=score.get, reverse=True)
