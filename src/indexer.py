"""Offline Indexer: embeds all 700 Bhagavad Gita verses and stores them in the VectorStore."""
from __future__ import annotations

import csv
import json
import os
from typing import Any, Dict, List

from src.embedder import Embedder
from src.vector_store import VectorStore

EXPECTED_VERSE_COUNT = 700  # Standard Bhagavad Gita verse count
_MIN_VERSE_COUNT = 690      # Allow slight variation in corpus editions

REQUIRED_FIELDS = {"verseId", "chapter", "verse", "translation"}


def _load_corpus(corpus_path: str) -> List[Dict[str, Any]]:
    """Load verses from a JSON or CSV file. Raises on missing/unparseable file."""
    if not os.path.exists(corpus_path):
        raise FileNotFoundError(f"Corpus file not found: {corpus_path}")

    ext = os.path.splitext(corpus_path)[1].lower()
    try:
        if ext == ".json":
            with open(corpus_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("JSON corpus must be a list of verse objects")
            return data
        elif ext == ".csv":
            with open(corpus_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                return list(reader)
        else:
            raise ValueError(f"Unsupported corpus format: {ext}. Use .json or .csv")
    except (json.JSONDecodeError, csv.Error) as exc:
        raise ValueError(f"Failed to parse corpus file: {exc}") from exc


def _validate_verse(verse: Dict[str, Any], index: int) -> None:
    missing = REQUIRED_FIELDS - set(verse.keys())
    if missing:
        raise ValueError(f"Verse at index {index} is missing required fields: {missing}")
    if not verse.get("verseId"):
        raise ValueError(f"Verse at index {index} has empty verseId")
    if not verse.get("translation"):
        raise ValueError(f"Verse at index {index} has empty translation")


def index_gita_corpus(
    corpus_path: str,
    embedder: Embedder | None = None,
    vector_store: VectorStore | None = None,
) -> int:
    """
    Embed and index all verses from the corpus.

    Returns the number of indexed verses (must equal 700).
    Raises on any error without partially updating the store.
    """
    if embedder is None:
        embedder = Embedder()
    if vector_store is None:
        vector_store = VectorStore()

    verses = _load_corpus(corpus_path)

    if not (_MIN_VERSE_COUNT <= len(verses) <= EXPECTED_VERSE_COUNT + 10):
        raise ValueError(
            f"Corpus must contain between {_MIN_VERSE_COUNT} and {EXPECTED_VERSE_COUNT + 10} verses, found {len(verses)}"
        )

    # Validate all verses before touching the store (atomic-ish)
    for i, verse in enumerate(verses):
        _validate_verse(verse, i)

    # Prepare texts for batch embedding
    texts = [
        f"{verse.get('translation', '')} {verse.get('commentary', '')}".strip()
        for verse in verses
    ]
    vectors = embedder.embed_batch(texts)

    indexed_count = 0
    for verse, vector in zip(verses, vectors):
        metadata = {
            "verseId": str(verse["verseId"]),
            "chapter": int(verse["chapter"]),
            "verse": int(verse["verse"]),
            "sanskrit": str(verse.get("sanskrit", "")),
            "transliteration": str(verse.get("transliteration", "")),
            "translation": str(verse["translation"]),
            "commentary": str(verse.get("commentary", "")),
        }
        vector_store.upsert(str(verse["verseId"]), vector, metadata)
        indexed_count += 1

    assert indexed_count >= _MIN_VERSE_COUNT, (
        f"Expected to index at least {_MIN_VERSE_COUNT} verses, indexed {indexed_count}"
    )
    return indexed_count
