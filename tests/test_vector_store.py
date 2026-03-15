"""Property-based and unit tests for VectorStore."""
import math
import random
import tempfile

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.models import VerseChunk
from src.vector_store import VectorStore


def _random_unit_vector(dim: int = 16, seed: int = 0) -> list[float]:
    rng = random.Random(seed)
    v = [rng.gauss(0, 1) for _ in range(dim)]
    mag = math.sqrt(sum(x * x for x in v))
    return [x / mag for x in v]


def _make_store() -> VectorStore:
    tmp = tempfile.mkdtemp()
    return VectorStore(persist_directory=tmp)


def _seed_store(store: VectorStore, n: int, dim: int = 16) -> None:
    for i in range(n):
        meta = {
            "verseId": f"{(i // 20) + 1}.{(i % 20) + 1}",
            "chapter": (i // 20) + 1,
            "verse": (i % 20) + 1,
            "sanskrit": f"sanskrit_{i}",
            "transliteration": f"trans_{i}",
            "translation": f"translation_{i}",
            "commentary": "",
        }
        store.upsert(f"verse_{i}", _random_unit_vector(dim, seed=i), meta)


# ---------------------------------------------------------------------------
# Property 10: Similarity search result ordering and bounds
# ---------------------------------------------------------------------------
@given(st.integers(min_value=1, max_value=10))
@settings(max_examples=20, deadline=None)
def test_similarity_search_ordering_and_bounds(top_k: int):
    """Results must be sorted descending by score and all scores in [0.0, 1.0]."""
    store = _make_store()
    _seed_store(store, n=20)
    query_vec = _random_unit_vector(16, seed=999)

    results = store.similarity_search(query_vec, top_k)

    assert len(results) <= top_k
    for chunk in results:
        assert 0.0 <= chunk.similarityScore <= 1.0

    scores = [c.similarityScore for c in results]
    assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# Unit: returns all available when store has fewer than top_k
# ---------------------------------------------------------------------------
def test_returns_all_when_fewer_than_topk():
    store = _make_store()
    _seed_store(store, n=3)
    results = store.similarity_search(_random_unit_vector(16, seed=42), top_k=10)
    assert len(results) == 3


# ---------------------------------------------------------------------------
# Unit: empty store returns empty list
# ---------------------------------------------------------------------------
def test_empty_store_returns_empty():
    store = _make_store()
    results = store.similarity_search(_random_unit_vector(16, seed=1), top_k=5)
    assert results == []


# ---------------------------------------------------------------------------
# Unit: delete_all clears the store
# ---------------------------------------------------------------------------
def test_delete_all():
    store = _make_store()
    _seed_store(store, n=5)
    assert store.count() == 5
    store.delete_all()
    assert store.count() == 0
