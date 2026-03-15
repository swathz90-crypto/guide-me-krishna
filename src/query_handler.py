"""QueryHandler: orchestrates the full RAG pipeline for Geetopadesha."""
from __future__ import annotations

import logging
import random
import uuid
from typing import List

from pydantic import ValidationError

from src.answer_generator import AnswerGenerator
from src.embedder import Embedder
from src.models import GeetaResponse, HealthStatus, QueryRequest, VerseChunk
from src.prompt_builder import PromptBuilder
from src.response_formatter import ResponseFormatter
from src.sanitizer import sanitize_query
from src.vector_store import VectorStore

logger = logging.getLogger(__name__)

_OUT_OF_SCOPE_THRESHOLD = 0.15

_OUT_OF_SCOPE_ANSWER = (
    "That's a beautiful question about life. The Bhagavad Gita may not address this exact topic directly, "
    "but its wisdom touches every corner of human experience. "
    "Try asking about the decision you're facing, the fear or doubt behind it, or what feels like your duty — "
    "and the Gita will have something meaningful and practical to say."
)


class QueryHandler:
    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        prompt_builder: PromptBuilder,
        answer_generator: AnswerGenerator,
        response_formatter: ResponseFormatter,
    ) -> None:
        self._embedder = embedder
        self._vector_store = vector_store
        self._prompt_builder = prompt_builder
        self._answer_generator = answer_generator
        self._formatter = response_formatter

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def handle_query(self, request: QueryRequest) -> GeetaResponse:
        """
        Process a validated QueryRequest through the full RAG pipeline.

        Pipeline: sanitize → embed → retrieve → out-of-scope check →
                  build prompt → generate → format
        """
        query_id = str(uuid.uuid4())

        # Step 1: Sanitize
        clean_query = sanitize_query(request.query)
        logger.info("queryId=%s stage=sanitize", query_id)

        # Step 2: Embed (with one retry on failure)
        query_vector = self._embed_with_retry(clean_query, query_id)

        # Step 3: Retrieve a larger candidate pool, then randomly sample topK from relevant ones
        _CANDIDATE_MULTIPLIER = 4
        candidate_k = min(request.topK * _CANDIDATE_MULTIPLIER, 20)
        try:
            candidates: List[VerseChunk] = self._vector_store.similarity_search(
                query_vector, candidate_k
            )
        except Exception as exc:
            logger.error("queryId=%s stage=retrieval error=%s", query_id, exc)
            raise

        # Step 4: Out-of-scope check on full candidate pool
        relevant = [v for v in candidates if v.similarityScore >= _OUT_OF_SCOPE_THRESHOLD]
        if not relevant:
            logger.info("queryId=%s stage=out_of_scope", query_id)
            closest = candidates[:1] if candidates else []
            return self._formatter.format(
                _OUT_OF_SCOPE_ANSWER, closest, language=request.language
            )

        # Randomly sample topK from relevant candidates (ensures variety across repeated queries)
        if len(relevant) > request.topK:
            verse_chunks = random.sample(relevant, request.topK)
            # Re-sort by score so prompt context is ordered best-first
            verse_chunks.sort(key=lambda v: v.similarityScore, reverse=True)
        else:
            verse_chunks = relevant

        # Step 5: Build prompt
        try:
            prompt = self._prompt_builder.build_prompt(clean_query, verse_chunks)
        except Exception as exc:
            logger.error("queryId=%s stage=prompt_builder error=%s", query_id, exc)
            raise

        # Step 6: Generate answer (retries handled inside AnswerGenerator)
        try:
            raw_answer = self._answer_generator.generate(prompt)
        except RuntimeError as exc:
            logger.error("queryId=%s stage=answer_generator error=%s", query_id, exc)
            raise

        # Step 7: Format response
        response = self._formatter.format(raw_answer, verse_chunks, language=request.language)
        logger.info("queryId=%s stage=complete confidence=%.3f", query_id, response.confidence)
        return response

    def health_check(self) -> HealthStatus:
        """Check reachability of all downstream components."""
        vs_ok = self._vector_store.is_reachable()
        emb_ok = self._embedder_reachable()
        llm_ok = self._answer_generator.is_reachable()

        overall = "ok" if all([vs_ok, emb_ok, llm_ok]) else "degraded"
        return HealthStatus(
            status=overall,
            vectorStore=vs_ok,
            embedder=emb_ok,
            answerGenerator=llm_ok,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _embed_with_retry(self, text: str, query_id: str) -> list[float]:
        try:
            return self._embedder.embed(text)
        except Exception as exc:
            logger.warning("queryId=%s stage=embed attempt=1 error=%s — retrying", query_id, exc)
            try:
                return self._embedder.embed(text)
            except Exception as exc2:
                logger.error("queryId=%s stage=embed attempt=2 error=%s", query_id, exc2)
                raise

    def _embedder_reachable(self) -> bool:
        try:
            self._embedder.embed("health check probe")
            return True
        except Exception:
            return False
