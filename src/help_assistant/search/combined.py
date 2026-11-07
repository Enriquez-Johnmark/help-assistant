"""Keyword and meaning search, combined by reciprocal rank fusion."""

from collections import defaultdict
from collections.abc import Sequence
from typing import Literal

from help_assistant.pages.reader import Passage
from help_assistant.search.embeddings import Embedder, cosine
from help_assistant.search.glossary import expand
from help_assistant.search.keyword import Hit, KeywordIndex

Mode = Literal["keyword", "combined"]

# How deep each list goes before the two are combined. Deeper lists added noise:
# on the Tagalog search questions, 5 found the right page for 24 of 25, 10 for
# 23 and 20 for 22. The test set checks the choice on questions it wasn't made on.
_DEPTH = 5


def fuse(rankings: Sequence[Sequence[str]], k: int = 60) -> list[str]:
    """Reciprocal rank fusion: each list adds 1 / (k + rank) to an item's score,
    so an item both lists rank highly comes first."""
    scores: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            scores[item] += 1 / (k + rank)
    return sorted(scores, key=lambda item: scores[item], reverse=True)


class Searcher:
    """Finds the passages that may answer a question. `mode` is "keyword" (BM25
    alone) or "combined" (BM25 and the embeddings), so the evaluation can compare
    them (F3)."""

    def __init__(self, passages: list[Passage], embedder: Embedder | None) -> None:
        self._passages = {passage.id: passage for passage in passages}
        self._keyword = KeywordIndex(passages)
        self._embedder = embedder
        self._vectors = embedder.embed([p.text for p in passages]) if embedder else []
        self._order = [passage.id for passage in passages]

    def search(self, query: str, k: int, mode: Mode = "combined") -> list[Hit]:
        if mode == "keyword":
            return self._keyword.search(expand(query), k)
        keyword = self._keyword.search(expand(query), _DEPTH)
        if self._embedder is None:
            raise ValueError("combined search needs the embedding model")
        [query_vector] = self._embedder.embed([query])
        similarity = {
            pid: cosine(query_vector, vector) for pid, vector in zip(self._order, self._vectors, strict=True)
        }
        meaning = sorted(similarity, key=lambda pid: similarity[pid], reverse=True)[:_DEPTH]
        fused = fuse([[hit.passage.id for hit in keyword], meaning])[:k]
        return [Hit(self._passages[pid], similarity[pid]) for pid in fused]
