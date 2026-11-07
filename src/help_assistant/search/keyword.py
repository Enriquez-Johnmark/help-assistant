"""Keyword search over passages: BM25."""

import math
import re
from collections import Counter
from dataclasses import dataclass

from help_assistant.pages.reader import Passage

_WORD = re.compile(r"[a-z0-9ñ]+")


def words(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def stem(word: str) -> str:
    """A light English stem, so "schools" finds "school" and "cancelling" finds
    "cancel". Short words are left alone."""
    for ending in ("ling", "ing", "ies", "es", "ed", "s"):
        if len(word) > len(ending) + 3 and word.endswith(ending):
            word = word[: -len(ending)]
            return word + "y" if ending == "ies" else word
    return word


def terms(text: str) -> list[str]:
    return [stem(word) for word in words(text)]


@dataclass(frozen=True)
class Hit:
    passage: Passage
    score: float


class KeywordIndex:
    """BM25 over the passages' words (k1 1.5, b 0.75)."""

    def __init__(self, passages: list[Passage], k1: float = 1.5, b: float = 0.75) -> None:
        self._passages = passages
        self._counts = [Counter(terms(p.text)) for p in passages]
        self._lengths = [sum(c.values()) for c in self._counts]
        self._average = sum(self._lengths) / len(self._lengths) if passages else 0.0
        documents = Counter(word for counts in self._counts for word in counts)
        total = len(passages)
        self._idf = {word: math.log(1 + (total - n + 0.5) / (n + 0.5)) for word, n in documents.items()}
        self._k1, self._b = k1, b

    def search(self, query: str, k: int) -> list[Hit]:
        """The `k` best passages for `query`; none for words no passage has."""
        query_terms = [term for term in terms(query) if term in self._idf]
        scored: list[Hit] = []
        for passage, counts, length in zip(self._passages, self._counts, self._lengths, strict=True):
            score = 0.0
            for term in query_terms:
                frequency = counts.get(term, 0)
                if frequency:
                    norm = frequency + self._k1 * (1 - self._b + self._b * length / self._average)
                    score += self._idf[term] * frequency * (self._k1 + 1) / norm
            if score > 0:
                scored.append(Hit(passage, score))
        return sorted(scored, key=lambda hit: hit.score, reverse=True)[:k]
