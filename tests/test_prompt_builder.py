"""Property-based and unit tests for PromptBuilder."""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.models import VerseChunk
from src.prompt_builder import MAX_CONTEXT_TOKENS, PromptBuilder, _estimate_tokens, SYSTEM_INSTRUCTION


def _make_verse(verse_id: str = "2.47", score: float = 0.9, translation: str = "Do your duty.") -> VerseChunk:
    return VerseChunk(
        verseId=verse_id,
        chapter=2,
        verse=47,
        sanskrit="कर्मण्येवाधिकारस्ते",
        transliteration="karmany evadhikaras te",
        translation=translation,
        commentary="Act without attachment to results.",
        similarityScore=score,
    )


verse_strategy = st.builds(
    VerseChunk,
    verseId=st.just("1.1"),
    chapter=st.just(1),
    verse=st.just(1),
    sanskrit=st.just("sanskrit"),
    transliteration=st.just("trans"),
    translation=st.text(min_size=1, max_size=200),
    commentary=st.text(min_size=0, max_size=100),
    similarityScore=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)


# ---------------------------------------------------------------------------
# Property 11: Prompt structure completeness
# ---------------------------------------------------------------------------
@given(
    query=st.text(min_size=1, max_size=200),
    verses=st.lists(verse_strategy, min_size=1, max_size=5),
)
@settings(max_examples=30)
def test_prompt_structure_completeness(query, verses):
    """fullText must contain system instruction, at least one verse, and the user query."""
    pb = PromptBuilder()
    prompt = pb.build_prompt(query, verses)

    assert SYSTEM_INSTRUCTION in prompt.fullText
    assert query in prompt.fullText
    # At least one verse chunk must appear in context
    assert len(prompt.verseContext) > 0


# ---------------------------------------------------------------------------
# Property 12: Token budget invariant
# ---------------------------------------------------------------------------
@given(
    query=st.text(min_size=1, max_size=200),
    verses=st.lists(verse_strategy, min_size=1, max_size=20),
)
@settings(max_examples=30)
def test_token_budget_invariant(query, verses):
    """fullText must never exceed MAX_CONTEXT_TOKENS."""
    pb = PromptBuilder()
    prompt = pb.build_prompt(query, verses)
    assert _estimate_tokens(prompt.fullText) <= MAX_CONTEXT_TOKENS


# ---------------------------------------------------------------------------
# Property 13: Verse truncation respects score ordering
# ---------------------------------------------------------------------------
def test_verse_truncation_respects_score_ordering():
    """When truncation occurs, lower-scored verses are excluded first."""
    # Create verses with distinct scores and large enough text to trigger truncation
    long_text = "A" * 400  # ~100 tokens each
    verses = [
        VerseChunk(verseId=f"1.{i}", chapter=1, verse=i, sanskrit="s", transliteration="t",
                   translation=long_text, commentary=long_text, similarityScore=round(1.0 - i * 0.1, 1))
        for i in range(1, 11)
    ]
    # Use a tight budget to force truncation
    pb = PromptBuilder(max_verse_context_tokens=300, max_context_tokens=2000)
    prompt = pb.build_prompt("test query", verses)

    # The highest-scored verse (1.1, score=0.9) must be included
    assert "1.1" in prompt.verseContext
    # The lowest-scored verse (1.10, score=0.0) should be excluded
    assert "1.10" not in prompt.verseContext


# ---------------------------------------------------------------------------
# Unit: empty query raises
# ---------------------------------------------------------------------------
def test_empty_query_raises():
    pb = PromptBuilder()
    with pytest.raises(ValueError):
        pb.build_prompt("", [_make_verse()])


# ---------------------------------------------------------------------------
# Unit: system instruction always present
# ---------------------------------------------------------------------------
def test_system_instruction_always_present():
    pb = PromptBuilder()
    prompt = pb.build_prompt("What is dharma?", [_make_verse()])
    assert prompt.systemInstruction == SYSTEM_INSTRUCTION
    assert SYSTEM_INSTRUCTION in prompt.fullText
