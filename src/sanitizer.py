"""Input sanitizer: strips control characters and special tokens from user queries."""
from __future__ import annotations

import re
import unicodedata

# Regex matching ASCII control characters (0x00–0x1F, 0x7F) except tab/newline/CR
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Common LLM prompt injection / special token patterns
_SPECIAL_TOKENS_RE = re.compile(
    r"<\|.*?\|>|<s>|</s>|<pad>|<unk>|<mask>|\[INST\]|\[/INST\]|\[SYS\]|\[/SYS\]",
    re.IGNORECASE,
)


def sanitize_query(query: str) -> str:
    """
    Remove control characters and special tokens from a user query.

    - Strips ASCII control characters (except \\t, \\n, \\r)
    - Removes LLM special tokens (e.g., <|endoftext|>, [INST], etc.)
    - Normalizes unicode to NFC form
    - Collapses multiple consecutive whitespace into a single space
    """
    # Normalize unicode
    text = unicodedata.normalize("NFC", query)
    # Remove control characters
    text = _CONTROL_CHARS_RE.sub("", text)
    # Remove special tokens
    text = _SPECIAL_TOKENS_RE.sub("", text)
    # Collapse multiple whitespace
    text = re.sub(r"[ \t]+", " ", text).strip()
    return text
