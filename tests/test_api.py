"""Integration tests for the FastAPI endpoints."""
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.models import GeetaResponse, HealthStatus, VerseChunk


def _make_mock_handler():
    mock = MagicMock()

    verse = VerseChunk(
        verseId="2.47", chapter=2, verse=47,
        sanskrit="कर्मण्येवाधिकारस्ते", transliteration="karmany evadhikaras te",
        translation="You have a right to perform your duties.",
        commentary="Act without attachment.", similarityScore=0.9,
    )
    mock.handle_query.return_value = GeetaResponse(
        answer="Do your duty without attachment.",
        citedVerses=[],
        language="en",
        queryId="test-id",
        confidence=0.9,
    )
    mock.health_check.return_value = HealthStatus(
        status="ok", vectorStore=True, embedder=True, answerGenerator=True
    )
    return mock


@pytest.fixture()
def client():
    os.environ.setdefault("OPENAI_API_KEY", "test-key")
    import src.main as main_module
    mock_handler = _make_mock_handler()
    main_module._handler = mock_handler
    with TestClient(main_module.app) as c:
        yield c
    main_module._handler = None


# ---------------------------------------------------------------------------
# POST /query — valid request
# ---------------------------------------------------------------------------
def test_query_valid(client):
    resp = client.post("/query", json={"query": "What is dharma?", "language": "en", "topK": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "queryId" in data


# ---------------------------------------------------------------------------
# POST /query — validation errors return 422 (FastAPI default for Pydantic v2)
# ---------------------------------------------------------------------------
def test_query_empty_query(client):
    resp = client.post("/query", json={"query": "", "language": "en", "topK": 5})
    assert resp.status_code == 422


def test_query_invalid_language(client):
    resp = client.post("/query", json={"query": "test", "language": "fr", "topK": 5})
    assert resp.status_code == 422


def test_query_invalid_topk(client):
    resp = client.post("/query", json={"query": "test", "language": "en", "topK": 0})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------
def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["vectorStore"] is True
    assert data["embedder"] is True
    assert data["answerGenerator"] is True
