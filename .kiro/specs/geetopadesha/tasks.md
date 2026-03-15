# Implementation Plan: Geetopadesha

## Overview

Python-based RAG application using FastAPI, sentence-transformers, ChromaDB, and an OpenAI-compatible LLM. Implementation proceeds in layers: data models → indexing pipeline → core RAG components → API layer → wiring.

## Tasks

- [x] 1. Set up project structure, dependencies, and core data models
  - Create `pyproject.toml` / `requirements.txt` with FastAPI, sentence-transformers, chromadb, openai, pydantic, python-dotenv, pytest, hypothesis
  - Create `src/models.py` with Pydantic models: `QueryRequest`, `VerseChunk`, `CitedVerse`, `GeetaResponse`, `Prompt`, `VerseMetadata`, `HealthStatus`
  - Enforce all validation rules on `QueryRequest` (non-empty query ≤ 1000 chars, language in ["en","hi","sa"], topK 1–10)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 7.3_

  - [x]* 1.1 Write property tests for QueryRequest validation
    - **Property 1: Whitespace queries are rejected**
    - **Property 2: Overlength queries are rejected**
    - **Property 3: Invalid language codes are rejected**
    - **Property 4: Out-of-range topK values are rejected**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

- [x] 2. Implement the Embedder component
  - Create `src/embedder.py` with `Embedder` class wrapping `sentence-transformers` (`paraphrase-multilingual-mpnet-base-v2`)
  - Implement `embed(text: str) -> list[float]` and `embed_batch(texts: list[str]) -> list[list[float]]`
  - L2-normalize output vectors; add LRU cache for repeated queries
  - _Requirements: 2.1, 2.2, 2.3_

  - [x]* 2.1 Write property tests for Embedder
    - **Property 5: Embedding fixed dimension**
    - **Property 6: Embedding L2 normalization**
    - **Property 7: Embedding determinism**
    - **Validates: Requirements 2.1, 2.2, 2.3**

- [x] 3. Implement the Vector Store component
  - Create `src/vector_store.py` with `VectorStore` class wrapping ChromaDB
  - Implement `upsert(id, vector, metadata)`, `similarity_search(query_vector, top_k) -> list[VerseChunk]`, `delete_all()`
  - Ensure results are sorted by similarity score descending and scores are in [0.0, 1.0]
  - _Requirements: 4.1, 4.2, 4.3_

  - [x]* 3.1 Write property tests for VectorStore
    - **Property 10: Similarity search result ordering and bounds**
    - **Validates: Requirements 4.1, 4.2**

- [x] 4. Implement the offline Indexer
  - Create `src/indexer.py` with `index_gita_corpus(corpus_path: str) -> int`
  - Load JSON/CSV corpus, assert exactly 700 verses, embed each verse (translation + commentary), upsert with full metadata
  - Halt with descriptive error if corpus is missing or unparseable; do not partially update the store
  - Create `scripts/run_indexer.py` as CLI entry point
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x]* 4.1 Write property tests for Indexer
    - **Property 8: Indexing completeness**
    - **Property 9: Indexed verse metadata completeness**
    - **Validates: Requirements 3.1, 3.2**

- [x] 5. Checkpoint — ensure all component tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement the Prompt Builder
  - Create `src/prompt_builder.py` with `PromptBuilder` class
  - Implement `build_prompt(query: str, verses: list[VerseChunk]) -> Prompt`
  - Include system instruction, add verse chunks in descending score order up to `MAX_VERSE_CONTEXT_TOKENS`, assemble `fullText` within `MAX_CONTEXT_TOKENS`
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.4_

  - [x]* 6.1 Write property tests for PromptBuilder
    - **Property 11: Prompt structure completeness**
    - **Property 12: Token budget invariant**
    - **Property 13: Verse truncation respects score ordering**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

- [x] 7. Implement the Answer Generator
  - Create `src/answer_generator.py` with `AnswerGenerator` class wrapping the OpenAI-compatible LLM API
  - Implement `generate(prompt: Prompt) -> str`
  - Retry up to 3 times with exponential backoff on 5xx / timeout; raise after exhausting retries
  - Read API key from environment variable; never hardcode
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 9.3_

- [x] 8. Implement the Response Formatter
  - Create `src/response_formatter.py` with `ResponseFormatter` class
  - Implement `format(raw_answer: str, verses: list[VerseChunk]) -> GeetaResponse`
  - Attach cited verses with Sanskrit, transliteration, translation; compute confidence as mean similarity score; generate unique `queryId` (UUID4); filter invalid verse references (chapter 1–18 only)
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x]* 8.1 Write property tests for ResponseFormatter
    - **Property 14: Response formatter output completeness**
    - **Property 15: Unique query IDs**
    - **Property 16: Confidence score accuracy**
    - **Property 17: Invalid verse references are filtered**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**

- [x] 9. Implement input sanitization
  - Add `sanitize_query(query: str) -> str` in `src/sanitizer.py` that strips control characters and special tokens
  - _Requirements: 9.1_

  - [x]* 9.1 Write property test for sanitizer
    - **Property 18: Query sanitization removes control characters**
    - **Validates: Requirements 9.1**

- [x] 10. Implement the Query Handler and wire the full RAG pipeline
  - Create `src/query_handler.py` with `QueryHandler` class
  - Implement `handle_query(request: QueryRequest) -> GeetaResponse` orchestrating: sanitize → validate → embed → retrieve → check out-of-scope (score < 0.3) → build prompt → generate → format
  - Implement `health_check() -> HealthStatus` pinging VectorStore, Embedder, and AnswerGenerator
  - Handle embedding retry (req 2.4), LLM retry with backoff (req 6.6), out-of-scope graceful refusal (req 8.1, 8.2, 8.3)
  - Log queryId, stage name, and error detail on any pipeline failure (req 10.3)
  - _Requirements: 1.1–1.5, 2.4, 4.4, 6.6, 8.1, 8.2, 8.3, 9.1, 10.1, 10.2, 10.3_

- [x] 11. Create the FastAPI application and rate limiting
  - Create `src/main.py` with FastAPI app
  - Mount `POST /query` → `QueryHandler.handle_query`, `GET /health` → `QueryHandler.health_check`
  - Add per-IP / per-session rate limiting middleware returning HTTP 429 when exceeded
  - Return HTTP 400 for validation errors, 429 for rate limit, 500/503 for upstream failures
  - _Requirements: 1.1–1.4, 9.2, 10.1_

- [x] 12. Final checkpoint — ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests use `hypothesis` and validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Run tests with: `pytest --tb=short`
