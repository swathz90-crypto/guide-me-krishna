"""Property-based and unit tests for the query sanitizer."""
import re

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.sanitizer import sanitize_query

# Control characters to inject (excluding \t, \n, \r which are allowed)
_CONTROL_CHARS = [chr(c) for c in range(0x00, 0x20) if chr(c) not in "\t\n\r"] + ["\x7f"]
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


# ---------------------------------------------------------------------------
# Property 18: Query sanitization removes control characters
# ---------------------------------------------------------------------------
@given(
    base=st.text(min_size=0, max_size=200),
    controls=st.lists(st.sampled_from(_CONTROL_CHARS), min_size=1, max_size=10),
)
@settings(max_examples=50)
def test_sanitization_removes_control_characters(base: str, controls: list[str]):
    """Any input containing control characters must have them removed after sanitization."""
    # Inject control chars at random positions
    import random
    chars = list(base)
    for c in controls:
        pos = random.randint(0, len(chars))
        chars.insert(pos, c)
    dirty = "".join(chars)

    clean = sanitize_query(dirty)

    assert not _CONTROL_CHARS_RE.search(clean), (
        f"Control characters found in sanitized output: {repr(clean)}"
    )


# ---------------------------------------------------------------------------
# Unit: special tokens are removed
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("token", [
    "<|endoftext|>", "<|im_start|>", "<s>", "</s>", "[INST]", "[/INST]", "[SYS]",
])
def test_special_tokens_removed(token: str):
    query = f"What is dharma? {token} Tell me more."
    clean = sanitize_query(query)
    assert token.lower() not in clean.lower()


# ---------------------------------------------------------------------------
# Unit: normal text is preserved
# ---------------------------------------------------------------------------
def test_normal_text_preserved():
    query = "How do I overcome fear and anxiety?"
    assert sanitize_query(query) == query


# ---------------------------------------------------------------------------
# Unit: unicode text is preserved
# ---------------------------------------------------------------------------
def test_unicode_preserved():
    query = "कर्म क्या है?"
    clean = sanitize_query(query)
    assert "कर्म" in clean
