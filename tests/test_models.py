"""Property-based and unit tests for QueryRequest validation."""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from src.models import QueryRequest

# ---------------------------------------------------------------------------
# Property 1: Whitespace-only queries are rejected
# ---------------------------------------------------------------------------
@given(st.text(alphabet=st.characters(whitelist_categories=("Zs", "Cc")), min_size=0, max_size=100))
def test_whitespace_query_rejected(whitespace_str: str):
    """Any string composed entirely of whitespace/control chars must be rejected."""
    with pytest.raises(ValidationError):
        QueryRequest(query=whitespace_str, language="en", topK=5)


# ---------------------------------------------------------------------------
# Property 2: Overlength queries are rejected
# ---------------------------------------------------------------------------
@given(st.text(min_size=1001, max_size=2000))
def test_overlength_query_rejected(long_query: str):
    """Any query longer than 1000 characters must be rejected."""
    with pytest.raises(ValidationError):
        QueryRequest(query=long_query, language="en", topK=5)


# ---------------------------------------------------------------------------
# Property 3: Invalid language codes are rejected
# ---------------------------------------------------------------------------
VALID_LANGS = {"en", "hi", "sa"}

@given(st.text(min_size=1, max_size=10).filter(lambda s: s not in VALID_LANGS))
def test_invalid_language_rejected(lang: str):
    """Any language code not in {en, hi, sa} must be rejected."""
    with pytest.raises(ValidationError):
        QueryRequest(query="valid query", language=lang, topK=5)


# ---------------------------------------------------------------------------
# Property 4: Out-of-range topK values are rejected
# ---------------------------------------------------------------------------
@given(st.integers().filter(lambda n: n < 1 or n > 10))
def test_out_of_range_topk_rejected(topk: int):
    """Any topK outside [1, 10] must be rejected."""
    with pytest.raises(ValidationError):
        QueryRequest(query="valid query", language="en", topK=topk)


# ---------------------------------------------------------------------------
# Unit tests: valid requests are accepted
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("lang", ["en", "hi", "sa"])
def test_valid_language_accepted(lang: str):
    req = QueryRequest(query="What is dharma?", language=lang, topK=5)
    assert req.language == lang


def test_valid_request_not_mutated():
    req = QueryRequest(query="  hello  ", language="en", topK=3)
    # The validator strips but the original object is frozen — value preserved as-is after strip check
    assert req.query == "  hello  "


def test_topk_boundary_values():
    for k in (1, 10):
        req = QueryRequest(query="test", language="en", topK=k)
        assert req.topK == k
