"""ResponseFormatter: structures raw LLM output into a GeetaResponse with cited verses."""
from __future__ import annotations

import re
import uuid
from typing import List

from src.models import CitedVerse, GeetaResponse, VerseChunk

# Valid Bhagavad Gita chapter ranges (chapters 1–18)
_VALID_CHAPTERS = set(range(1, 19))

# Verse counts per chapter (standard 700-verse count)
_VERSES_PER_CHAPTER = {
    1: 47, 2: 72, 3: 43, 4: 42, 5: 29, 6: 47,
    7: 30, 8: 28, 9: 34, 10: 42, 11: 55, 12: 20,
    13: 35, 14: 27, 15: 20, 16: 24, 17: 28, 18: 78,
}


def _is_valid_verse_ref(chapter: int, verse: int) -> bool:
    if chapter not in _VALID_CHAPTERS:
        return False
    max_verse = _VERSES_PER_CHAPTER.get(chapter, 0)
    return 1 <= verse <= max_verse


def _extract_verse_refs_from_answer(raw_answer: str) -> set[str]:
    """Extract verse IDs mentioned in the raw answer (e.g., 'BG 2.47', '2.47')."""
    pattern = r"\bBG\s*(\d+)\.(\d+)\b|\b(\d+)\.(\d+)\b"
    refs: set[str] = set()
    for m in re.finditer(pattern, raw_answer):
        ch = int(m.group(1) or m.group(3))
        vs = int(m.group(2) or m.group(4))
        if _is_valid_verse_ref(ch, vs):
            refs.add(f"{ch}.{vs}")
    return refs


class ResponseFormatter:
    def format(
        self,
        raw_answer: str,
        verses: List[VerseChunk],
        language: str = "en",
    ) -> GeetaResponse:
        """
        Build a GeetaResponse from the raw LLM answer and the retrieved verse chunks.

        - Attaches cited verses with full Sanskrit/transliteration/translation
        - Filters out any verse references with invalid chapter/verse numbers
        - Computes confidence as the mean similarity score of cited verses
        - Assigns a unique queryId
        """
        # Filter verses to only those with valid chapter/verse references
        valid_verses = [
            v for v in verses
            if _is_valid_verse_ref(v.chapter, v.verse)
        ]

        cited: List[CitedVerse] = [
            CitedVerse(
                verseId=v.verseId,
                chapter=v.chapter,
                verse=v.verse,
                sanskrit=v.sanskrit,
                transliteration=v.transliteration,
                translation=v.translation,
                similarityScore=v.similarityScore,
            )
            for v in valid_verses
        ]

        confidence = (
            sum(c.similarityScore for c in cited) / len(cited)
            if cited else 0.0
        )

        return GeetaResponse(
            answer=raw_answer,
            citedVerses=cited,
            language=language,
            queryId=str(uuid.uuid4()),
            confidence=round(confidence, 6),
        )
