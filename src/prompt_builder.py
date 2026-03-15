"""PromptBuilder: assembles the augmented LLM prompt from query and retrieved verses."""
from __future__ import annotations

from typing import List

from src.models import Prompt, VerseChunk

# Token budget constants (approximate; 1 token ≈ 4 chars for English)
MAX_VERSE_CONTEXT_TOKENS = 2048
MAX_CONTEXT_TOKENS = 4096

SYSTEM_INSTRUCTION = (
    "You are Geetopadesha, a warm and caring spiritual guide. You speak like a wise elder friend — "
    "simple, clear, and straight from the heart. No complicated words, no religious jargon.\n\n"
    "Use ONLY the provided Bhagavad Gita verses to answer. Do not bring in outside teachings.\n\n"
    "How to respond:\n"
    "1. Start with a warm, direct answer to the person's question in plain everyday language. "
    "Speak as if you are talking to someone who has never read the Gita. "
    "Use short sentences. Be practical. Make them feel understood.\n"
    "2. For practical life questions — career choices, marriage, relationships, money, family — "
    "apply the Gita's wisdom directly. The Gita speaks to ALL of life: duty, desire, attachment, "
    "decision-making, relationships. Find the relevant teaching and connect it to the question.\n"
    "3. Then for EACH verse provided, explain: what this verse is saying in simple words, "
    "AND specifically how it connects to what the person just asked. "
    "Make it feel personal — like you are applying the verse directly to their situation.\n"
    "4. Always mention the verse number (e.g., BG 2.47) when referring to it.\n\n"
    "Important:\n"
    "- If someone asks about predicting their future (e.g., 'will I have a love marriage?', "
    "'what will happen to me?'), gently say the Gita does not predict futures, "
    "but it can guide HOW to approach that decision — then give that guidance warmly.\n"
    "- Write like you are talking to a friend, not giving a lecture\n"
    "- No Sanskrit words without immediately explaining them in brackets\n"
    "- Keep paragraphs short — 2 to 3 sentences each\n"
    "- Focus only on verses that are truly relevant to the question\n"
    "- End with one encouraging sentence that feels personal and warm"
)


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: 1 token ≈ 4 characters."""
    return max(1, len(text) // 4)


class PromptBuilder:
    def __init__(
        self,
        max_verse_context_tokens: int = MAX_VERSE_CONTEXT_TOKENS,
        max_context_tokens: int = MAX_CONTEXT_TOKENS,
    ) -> None:
        self._max_verse_tokens = max_verse_context_tokens
        self._max_context_tokens = max_context_tokens

    def build_prompt(self, query: str, verses: List[VerseChunk]) -> Prompt:
        """
        Build an augmented prompt from the user query and retrieved verse chunks.

        Verses are included in descending similarity score order up to the token budget.
        """
        if not query:
            raise ValueError("query must be non-empty")

        # Sort verses by similarity score descending (defensive — should already be sorted)
        sorted_verses = sorted(verses, key=lambda v: v.similarityScore, reverse=True)

        verse_context = ""
        token_count = 0

        for chunk in sorted_verses:
            chunk_text = (
                f"BG {chunk.verseId}: {chunk.translation}\n"
                f"{chunk.commentary}\n\n"
            )
            chunk_tokens = _estimate_tokens(chunk_text)
            if token_count + chunk_tokens <= self._max_verse_tokens:
                verse_context += chunk_text
                token_count += chunk_tokens

        full_text = (
            f"SYSTEM: {SYSTEM_INSTRUCTION}\n\n"
            f"CONTEXT (Bhagavad Gita Verses):\n{verse_context}\n"
            f"USER QUESTION: {query}\n"
            f"ANSWER:"
        )

        # Safety truncation if full_text somehow exceeds max context
        if _estimate_tokens(full_text) > self._max_context_tokens:
            # Trim verse context further
            allowed_chars = self._max_context_tokens * 4
            overhead = len(full_text) - len(verse_context)
            verse_context = verse_context[: max(0, allowed_chars - overhead)]
            full_text = (
                f"SYSTEM: {SYSTEM_INSTRUCTION}\n\n"
                f"CONTEXT (Bhagavad Gita Verses):\n{verse_context}\n"
                f"USER QUESTION: {query}\n"
                f"ANSWER:"
            )

        return Prompt(
            systemInstruction=SYSTEM_INSTRUCTION,
            verseContext=verse_context,
            userQuery=query,
            fullText=full_text,
        )
