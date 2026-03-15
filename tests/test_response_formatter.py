"""Property-based and unit tests for ResponseFormatter."""
import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.models import VerseChunk
from src.response_formatter import ResponseFormatter, _is_valid_verse_ref

formatter = ResponseFormatter()


def _make_verse(chapter: int = 2, verse: int = 47, score: float = 0.8) -> VerseChunk:
    return VerseChunk(
        verseId=f"{chapter}.{verse}",
        chapter=chapter,
        verse=verse,
        sanskrit="कर्मण्येवाधिकारस्ते",
        transliteration="karmany evadhikaras te",
        translation="You have a right to perform your duties.",
        commentary="Act without attachment.",
        similarityScore=score,
    )


valid_verse_strategy = st.builds(
    VerseChunk,
    verseId=st.just("2.47"),
    chapter=st.just(2),
    verse=st.just(47),
    sanskrit=st.just("sanskrit"),
    transliteration=st.just("trans"),
    translation=st.text(min_size=1, max_size=100),
    commentary=st.text(min_size=0, max_size=50),
    similarityScore=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)


# ---------------------------------------------------------------------------
# Property 14: Response formatter output completeness
# ---------------------------------------------------------------------------
@given(
    raw_answer=st.text(min_size=1, max_size=500),
    verses=st.lists(valid_verse_strategy, min_size=1, max_size=5),
)
@settings(max_examples=30)
def test_formatter_output_completeness(raw_answer, verses):
    """GeetaResponse must have non-empty answer and at least one CitedVerse with required fields."""
    response = formatter.format(raw_answer, verses)

    assert response.answer == raw_answer
    assert len(response.citedVerses) >= 1
    for cv in response.citedVerses:
        assert cv.sanskrit
        assert cv.transliteration
        assert cv.translation


# ---------------------------------------------------------------------------
# Property 15: Unique query IDs
# ---------------------------------------------------------------------------
@given(
    raw_answer=st.text(min_size=1, max_size=100),
)
@settings(max_examples=30)
def test_unique_query_ids(raw_answer):
    """Two independently formatted responses must have distinct queryIds."""
    r1 = formatter.format(raw_answer, [_make_verse()])
    r2 = formatter.format(raw_answer, [_make_verse()])
    assert r1.queryId != r2.queryId


# ---------------------------------------------------------------------------
# Property 16: Confidence score accuracy
# ---------------------------------------------------------------------------
@given(
    scores=st.lists(st.floats(min_value=0.0, max_value=1.0, allow_nan=False), min_size=1, max_size=10),
)
@settings(max_examples=30)
def test_confidence_score_accuracy(scores):
    """confidence must equal the arithmetic mean of cited verse similarity scores."""
    verses = [_make_verse(chapter=2, verse=47, score=s) for s in scores]
    response = formatter.format("some answer", verses)
    expected = sum(scores) / len(scores)
    assert abs(response.confidence - expected) < 1e-4


# ---------------------------------------------------------------------------
# Property 17: Invalid verse references are filtered
# ---------------------------------------------------------------------------
def test_invalid_verse_references_filtered():
    """Verses with chapter > 18 or invalid verse numbers must be excluded from citedVerses."""
    valid = _make_verse(chapter=2, verse=47, score=0.9)
    invalid_chapter = VerseChunk(
        verseId="99.1", chapter=99, verse=1,
        sanskrit="s", transliteration="t", translation="t",
        commentary="", similarityScore=0.8,
    )
    invalid_verse = VerseChunk(
        verseId="1.999", chapter=1, verse=999,
        sanskrit="s", transliteration="t", translation="t",
        commentary="", similarityScore=0.7,
    )

    response = formatter.format("answer", [valid, invalid_chapter, invalid_verse])

    verse_ids = {cv.verseId for cv in response.citedVerses}
    assert "2.47" in verse_ids
    assert "99.1" not in verse_ids
    assert "1.999" not in verse_ids


# ---------------------------------------------------------------------------
# Unit: queryId is a valid UUID
# ---------------------------------------------------------------------------
def test_query_id_is_uuid():
    import uuid
    response = formatter.format("answer", [_make_verse()])
    uuid.UUID(response.queryId)  # raises if not valid UUID
