"""Meaning search with a small multilingual model run locally: no paid service,
and a Tagalog question can find an English page."""

import os
from collections.abc import Sequence
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

Vector = NDArray[np.float32]


class Embedder(Protocol):
    def embed(self, texts: Sequence[str]) -> list[Vector]: ...


class FastEmbedder:
    """The local model, downloaded once into `HELP_ASSISTANT_MODELS` (default `data/models`)."""

    def __init__(self, model: str = MODEL) -> None:
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model, cache_dir=os.environ.get("HELP_ASSISTANT_MODELS", "data/models"))

    def embed(self, texts: Sequence[str]) -> list[Vector]:
        return [np.asarray(vector, dtype=np.float32) for vector in self._model.embed(list(texts))]


def cosine(a: Vector, b: Vector) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
