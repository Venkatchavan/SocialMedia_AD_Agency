"""Vector store for semantic ad search (U-10).

Abstracts ChromaDB (local) / Qdrant (production) behind a common interface.
Indexes: AoT atoms, insights, hook patterns, generated content performance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import math

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class VectorDocument:
    """A document to index in the vector store."""

    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    workspace_id: str = ""
    collection: str = "default"


@dataclass
class SearchResult:
    """A single search result from vector query."""

    id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorStore:
    """In-memory vector store with cosine similarity.

    For production, swap with ChromaDB or Qdrant client.
    This implementation uses simple TF-based vectors for testing.
    """

    def __init__(self) -> None:
        # collection_name → list of (id, text, metadata, vector)
        self._collections: dict[str, list[dict[str, Any]]] = {}

    def create_collection(self, name: str) -> None:
        """Create a named collection."""
        if name not in self._collections:
            self._collections[name] = []

    def add(self, doc: VectorDocument) -> None:
        """Add a document to the vector store."""
        self.create_collection(doc.collection)
        vector = self._text_to_vector(doc.text)
        self._collections[doc.collection].append({
            "id": doc.id,
            "text": doc.text,
            "metadata": {**doc.metadata, "workspace_id": doc.workspace_id},
            "vector": vector,
        })

    def add_batch(self, docs: list[VectorDocument]) -> int:
        """Add multiple documents. Returns count added."""
        for doc in docs:
            self.add(doc)
        return len(docs)

    def search(
        self,
        query: str,
        collection: str = "default",
        workspace_id: str = "",
        top_k: int = 5,
    ) -> list[SearchResult]:
        """Search for similar documents using cosine similarity."""
        if collection not in self._collections:
            return []

        query_vector = self._text_to_vector(query)
        docs = self._collections[collection]

        # Filter by workspace if specified
        if workspace_id:
            docs = [d for d in docs if d["metadata"].get("workspace_id") == workspace_id]

        scored: list[tuple[float, dict]] = []
        for doc in docs:
            sim = self._cosine_similarity(query_vector, doc["vector"])
            scored.append((sim, doc))

        scored.sort(key=lambda x: x[0], reverse=True)

        results: list[SearchResult] = []
        for score, doc in scored[:top_k]:
            results.append(SearchResult(
                id=doc["id"],
                text=doc["text"],
                score=round(score, 4),
                metadata=doc["metadata"],
            ))
        return results

    def delete(self, doc_id: str, collection: str = "default") -> bool:
        """Delete a document by ID."""
        if collection not in self._collections:
            return False
        before = len(self._collections[collection])
        self._collections[collection] = [
            d for d in self._collections[collection] if d["id"] != doc_id
        ]
        return len(self._collections[collection]) < before

    def count(self, collection: str = "default") -> int:
        """Count documents in a collection."""
        return len(self._collections.get(collection, []))

    def list_collections(self) -> list[str]:
        """List all collection names."""
        return list(self._collections.keys())

    def _text_to_vector(self, text: str) -> dict[str, float]:
        """Simple term-frequency vector for testing.

        Production: use embedding model (OpenAI, sentence-transformers).
        """
        words = text.lower().split()
        freq: dict[str, float] = {}
        for word in words:
            word = word.strip(".,!?;:'\"()[]{}").lower()
            if len(word) > 1:
                freq[word] = freq.get(word, 0) + 1
        # Normalize
        total = sum(freq.values()) or 1
        return {k: v / total for k, v in freq.items()}

    def _cosine_similarity(
        self, vec_a: dict[str, float], vec_b: dict[str, float]
    ) -> float:
        """Compute cosine similarity between two sparse vectors."""
        keys = set(vec_a.keys()) | set(vec_b.keys())
        dot = sum(vec_a.get(k, 0) * vec_b.get(k, 0) for k in keys)
        mag_a = math.sqrt(sum(v * v for v in vec_a.values())) or 1e-10
        mag_b = math.sqrt(sum(v * v for v in vec_b.values())) or 1e-10
        return dot / (mag_a * mag_b)
