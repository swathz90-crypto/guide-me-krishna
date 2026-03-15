"""VectorStore: persists verse embeddings and performs cosine similarity search via ChromaDB."""
from __future__ import annotations

from typing import Any, Dict, List

import chromadb
from chromadb.config import Settings

from src.models import VerseChunk

_COLLECTION_NAME = "gita_verses"


class VectorStore:
    def __init__(self, persist_directory: str = ".chroma") -> None:
        self._client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def upsert(self, id: str, vector: List[float], metadata: Dict[str, Any]) -> None:
        """Insert or update a verse embedding with its metadata."""
        self._collection.upsert(
            ids=[id],
            embeddings=[vector],
            metadatas=[metadata],
        )

    def similarity_search(self, query_vector: List[float], top_k: int) -> List[VerseChunk]:
        """Return up to top_k VerseChunks sorted by similarity score descending."""
        if top_k < 1 or top_k > 20:
            raise ValueError("top_k must be between 1 and 20")

        count = self._collection.count()
        if count == 0:
            return []

        n_results = min(top_k, count)
        results = self._collection.query(
            query_embeddings=[query_vector],
            n_results=n_results,
            include=["metadatas", "distances"],
        )

        chunks: List[VerseChunk] = []
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for meta, dist in zip(metadatas, distances):
            # ChromaDB cosine distance = 1 - cosine_similarity
            similarity = max(0.0, min(1.0, 1.0 - dist))
            chunks.append(
                VerseChunk(
                    verseId=meta.get("verseId", ""),
                    chapter=int(meta.get("chapter", 0)),
                    verse=int(meta.get("verse", 0)),
                    sanskrit=meta.get("sanskrit", ""),
                    transliteration=meta.get("transliteration", ""),
                    translation=meta.get("translation", ""),
                    commentary=meta.get("commentary", ""),
                    similarityScore=similarity,
                )
            )

        # Ensure descending order by similarity score
        chunks.sort(key=lambda c: c.similarityScore, reverse=True)
        return chunks

    def delete_all(self) -> None:
        """Remove all entries from the collection."""
        self._client.delete_collection(_COLLECTION_NAME)
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        return self._collection.count()

    def is_reachable(self) -> bool:
        try:
            self._collection.count()
            return True
        except Exception:
            return False
