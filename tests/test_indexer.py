"""Property-based and unit tests for the offline Indexer."""
import json
import math
import random
import tempfile
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.indexer import EXPECTED_VERSE_COUNT, index_gita_corpus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_verse(i: int) -> Dict[str, Any]:
    chapter = (i // 20) + 1
    verse_num = (i % 20) + 1
    return {
        "verseId": f"{chapter}.{verse_num}",
        "chapter": chapter,
        "verse": verse_num,
        "sanskrit": f"sanskrit_{i}",
        "transliteration": f"trans_{i}",
        "translation": f"translation text for verse {i}",
        "commentary": f"commentary for verse {i}",
    }


def _make_corpus_file(verses: List[Dict[str, Any]]) -> str:
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8")
    json.dump(verses, tmp)
    tmp.close()
    return tmp.name


def _make_mock_embedder(dim: int = 16):
    mock = MagicMock()

    def embed_batch(texts):
        result = []
        for t in texts:
            rng = random.Random(abs(hash(t)) % (2**32))
            v = [rng.gauss(0, 1) for _ in range(dim)]
            mag = math.sqrt(sum(x * x for x in v))
            result.append([x / mag for x in v])
        return result

    mock.embed_batch.side_effect = embed_batch
    return mock


def _make_mock_store():
    mock = MagicMock()
    mock.upsert.return_value = None
    return mock


# ---------------------------------------------------------------------------
# Property 8: Indexing completeness
# ---------------------------------------------------------------------------
def test_indexing_completeness():
    """After indexing a valid 700-verse corpus, indexed count must equal 700."""
    verses = [_make_verse(i) for i in range(EXPECTED_VERSE_COUNT)]
    corpus_path = _make_corpus_file(verses)
    embedder = _make_mock_embedder()
    store = _make_mock_store()

    count = index_gita_corpus(corpus_path, embedder=embedder, vector_store=store)

    assert count == EXPECTED_VERSE_COUNT
    assert store.upsert.call_count == EXPECTED_VERSE_COUNT


# ---------------------------------------------------------------------------
# Property 9: Indexed verse metadata completeness
# ---------------------------------------------------------------------------
def test_indexed_verse_metadata_completeness():
    """Every upserted verse must include all required metadata fields."""
    verses = [_make_verse(i) for i in range(EXPECTED_VERSE_COUNT)]
    corpus_path = _make_corpus_file(verses)
    embedder = _make_mock_embedder()
    store = _make_mock_store()

    index_gita_corpus(corpus_path, embedder=embedder, vector_store=store)

    required_keys = {"verseId", "chapter", "verse", "sanskrit", "transliteration", "translation", "commentary"}
    for call in store.upsert.call_args_list:
        _, kwargs = call
        # upsert(id, vector, metadata) — positional args
        args = call[0]
        metadata = args[2]
        assert required_keys.issubset(set(metadata.keys())), f"Missing keys in metadata: {metadata}"


# ---------------------------------------------------------------------------
# Unit: wrong verse count raises
# ---------------------------------------------------------------------------
def test_wrong_verse_count_raises():
    verses = [_make_verse(i) for i in range(10)]  # only 10, not 700
    corpus_path = _make_corpus_file(verses)
    with pytest.raises(ValueError, match="exactly"):
        index_gita_corpus(corpus_path, embedder=_make_mock_embedder(), vector_store=_make_mock_store())


# ---------------------------------------------------------------------------
# Unit: missing corpus file raises FileNotFoundError
# ---------------------------------------------------------------------------
def test_missing_corpus_raises():
    with pytest.raises(FileNotFoundError):
        index_gita_corpus("/nonexistent/path/corpus.json")


# ---------------------------------------------------------------------------
# Unit: missing required field raises ValueError
# ---------------------------------------------------------------------------
def test_missing_required_field_raises():
    verses = [_make_verse(i) for i in range(EXPECTED_VERSE_COUNT)]
    del verses[0]["translation"]  # remove required field
    corpus_path = _make_corpus_file(verses)
    with pytest.raises(ValueError, match="missing required fields"):
        index_gita_corpus(corpus_path, embedder=_make_mock_embedder(), vector_store=_make_mock_store())
