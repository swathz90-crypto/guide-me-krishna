"""Property-based tests for the Embedder component."""
import math
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# We mock SentenceTransformer so tests run without downloading the model.
import numpy as np


def _make_mock_model(dim: int = 768):
    """Return a mock SentenceTransformer that produces deterministic unit vectors."""
    mock = MagicMock()

    def encode(texts, normalize_embeddings=True, show_progress_bar=False):
        vecs = []
        for t in texts:
            # Deterministic: hash-based seed so same text → same vector
            rng = np.random.default_rng(abs(hash(t)) % (2**32))
            v = rng.standard_normal(dim).astype(np.float32)
            if normalize_embeddings:
                v = v / np.linalg.norm(v)
            vecs.append(v)
        return np.array(vecs)

    mock.encode.side_effect = encode
    return mock


@pytest.fixture()
def embedder():
    with patch("src.embedder.SentenceTransformer", return_value=_make_mock_model(768)):
        from src.embedder import Embedder
        return Embedder()


# ---------------------------------------------------------------------------
# Property 5: Fixed dimension
# ---------------------------------------------------------------------------
@given(st.text(min_size=1, max_size=500).filter(lambda t: t.strip()))
@settings(max_examples=30)
def test_embedding_fixed_dimension(text: str):
    """embed() must always return a vector of the same fixed dimension."""
    with patch("src.embedder.SentenceTransformer", return_value=_make_mock_model(768)):
        from src.embedder import Embedder
        e = Embedder()
        v1 = e.embed(text)
        v2 = e.embed("another text entirely")
        assert len(v1) == len(v2)


# ---------------------------------------------------------------------------
# Property 6: L2 normalization
# ---------------------------------------------------------------------------
@given(st.text(min_size=1, max_size=500).filter(lambda t: t.strip()))
@settings(max_examples=30)
def test_embedding_l2_normalized(text: str):
    """embed() must return a vector with magnitude ≈ 1.0."""
    with patch("src.embedder.SentenceTransformer", return_value=_make_mock_model(768)):
        from src.embedder import Embedder
        e = Embedder()
        v = e.embed(text)
        magnitude = math.sqrt(sum(x * x for x in v))
        assert abs(magnitude - 1.0) < 1e-5


# ---------------------------------------------------------------------------
# Property 7: Determinism
# ---------------------------------------------------------------------------
@given(st.text(min_size=1, max_size=500).filter(lambda t: t.strip()))
@settings(max_examples=30)
def test_embedding_deterministic(text: str):
    """Embedding the same text twice must produce identical vectors."""
    with patch("src.embedder.SentenceTransformer", return_value=_make_mock_model(768)):
        from src.embedder import Embedder
        e = Embedder()
        v1 = e.embed(text)
        v2 = e.embed(text)
        assert v1 == v2


# ---------------------------------------------------------------------------
# Unit: empty text raises ValueError
# ---------------------------------------------------------------------------
def test_embed_empty_raises(embedder):
    with pytest.raises(ValueError):
        embedder.embed("")

    with pytest.raises(ValueError):
        embedder.embed("   ")
