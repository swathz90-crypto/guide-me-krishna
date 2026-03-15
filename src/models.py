"""Core Pydantic data models for Geetopadesha."""
from __future__ import annotations

import uuid
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class QueryRequest(BaseModel):
    query: str = Field(..., description="User's natural language question")
    language: str = Field(default="en", description="Response language: en, hi, sa")
    topK: int = Field(default=5, ge=1, le=10, description="Number of verses to retrieve")
    sessionId: Optional[str] = Field(default=None, description="Optional session identifier")

    @field_validator("query")
    @classmethod
    def query_must_be_non_empty(cls, v: str) -> str:
        import unicodedata
        # Strip whitespace and Unicode control/format characters before checking emptiness
        stripped = "".join(
            c for c in v
            if not (c.isspace() or unicodedata.category(c) in ("Cc", "Cf", "Cs"))
        )
        if not stripped:
            raise ValueError("query must not be empty or whitespace/control-char-only")
        if len(v) > 1000:
            raise ValueError("query must not exceed 1000 characters")
        return v

    @field_validator("language")
    @classmethod
    def language_must_be_valid(cls, v: str) -> str:
        if v not in ("en", "hi", "sa"):
            raise ValueError("language must be one of: en, hi, sa")
        return v

    model_config = {"frozen": True}


class VerseChunk(BaseModel):
    verseId: str
    chapter: int
    verse: int
    sanskrit: str
    transliteration: str
    translation: str
    commentary: str = ""
    similarityScore: float = Field(default=0.0, ge=0.0, le=1.0)


class CitedVerse(BaseModel):
    verseId: str
    chapter: int
    verse: int
    sanskrit: str
    transliteration: str
    translation: str
    similarityScore: float = Field(default=0.0, ge=0.0, le=1.0)


class GeetaResponse(BaseModel):
    answer: str
    citedVerses: List[CitedVerse]
    language: str
    queryId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Prompt(BaseModel):
    systemInstruction: str
    verseContext: str
    userQuery: str
    fullText: str


class VerseMetadata(BaseModel):
    chapter: int
    verse: int
    sanskrit: str
    transliteration: str
    translation: str
    commentary: str = ""


class HealthStatus(BaseModel):
    status: str  # "ok" or "degraded"
    vectorStore: bool
    embedder: bool
    answerGenerator: bool
