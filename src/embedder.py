"""Embedder: converts text to L2-normalized dense vectors using sentence-transformers."""
from __future__ import annotations

import math
import os
from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

_MODEL_NAME = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


class Embedder:
    def __init__(self, model_name: str = _MODEL_NAME) -> None:
        self._model = SentenceTransformer(model_name)
        self._dim: int | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed(self, text: str) -> List[float]:
        """Embed a single text string and return an L2-normalized vector."""
        if not text or not text.strip():
            raise ValueError("text must be non-empty")
        return self._embed_cached(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts in one batch call."""
        if not texts:
            return []
        raw = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [v.tolist() for v in raw]

    @property
    def dimension(self) -> int:
        if self._dim is None:
            self._dim = len(self.embed("probe"))
        return self._dim

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @lru_cache(maxsize=512)
    def _embed_cached(self, text: str) -> List[float]:
        raw = self._model.encode([text], normalize_embeddings=True, show_progress_bar=False)
        return raw[0].tolist()


def _l2_norm(vec: List[float]) -> float:
    return math.sqrt(sum(x * x for x in vec))
