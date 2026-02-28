"""Tests for vector store / semantic ad search (U-10)."""

from __future__ import annotations

import pytest

from app.db.vector_store import VectorStore, VectorDocument, SearchResult


@pytest.fixture
def store() -> VectorStore:
    """Fresh vector store for each test."""
    return VectorStore()


class TestVectorStoreBasics:
    def test_create_collection(self, store: VectorStore):
        store.create_collection("ads")
        assert "ads" in store.list_collections()

    def test_add_document(self, store: VectorStore):
        doc = VectorDocument(id="1", text="fear based hook in SaaS", collection="ads")
        store.add(doc)
        assert store.count("ads") == 1

    def test_add_batch(self, store: VectorStore):
        docs = [
            VectorDocument(id="1", text="SaaS comparison ad", collection="ads"),
            VectorDocument(id="2", text="e-commerce product demo", collection="ads"),
            VectorDocument(id="3", text="fitness transformation story", collection="ads"),
        ]
        count = store.add_batch(docs)
        assert count == 3
        assert store.count("ads") == 3

    def test_delete_document(self, store: VectorStore):
        store.add(VectorDocument(id="1", text="test", collection="ads"))
        assert store.delete("1", "ads")
        assert store.count("ads") == 0

    def test_delete_nonexistent(self, store: VectorStore):
        assert not store.delete("999", "ads")


class TestVectorSearch:
    def test_search_returns_results(self, store: VectorStore):
        store.add(VectorDocument(id="1", text="fear based hook marketing SaaS", collection="ads"))
        store.add(VectorDocument(id="2", text="happy positive lifestyle fitness", collection="ads"))
        store.add(VectorDocument(id="3", text="fear scarcity urgency SaaS marketing", collection="ads"))

        results = store.search("fear based hooks in SaaS vertical", collection="ads")
        assert len(results) > 0
        # The fear/SaaS docs should rank higher
        ids = [r.id for r in results]
        assert ids[0] in ("1", "3")

    def test_search_top_k(self, store: VectorStore):
        for i in range(10):
            store.add(VectorDocument(id=str(i), text=f"document number {i}", collection="ads"))
        results = store.search("document", collection="ads", top_k=3)
        assert len(results) == 3

    def test_search_empty_collection(self, store: VectorStore):
        results = store.search("anything", collection="empty")
        assert results == []

    def test_search_workspace_isolation(self, store: VectorStore):
        store.add(VectorDocument(id="1", text="ad for brand A", collection="ads", workspace_id="ws1"))
        store.add(VectorDocument(id="2", text="ad for brand B", collection="ads", workspace_id="ws2"))

        results = store.search("ad for brand", collection="ads", workspace_id="ws1")
        assert len(results) == 1
        assert results[0].id == "1"

    def test_search_score_range(self, store: VectorStore):
        store.add(VectorDocument(id="1", text="test query match", collection="ads"))
        results = store.search("test query match", collection="ads")
        assert len(results) == 1
        assert 0.0 <= results[0].score <= 1.0

    def test_search_result_has_metadata(self, store: VectorStore):
        store.add(VectorDocument(
            id="1", text="SaaS ad", collection="ads",
            metadata={"platform": "instagram", "hook_type": "fear"},
        ))
        results = store.search("SaaS", collection="ads")
        assert results[0].metadata["platform"] == "instagram"


class TestVectorDocument:
    def test_defaults(self):
        doc = VectorDocument(id="1", text="test")
        assert doc.collection == "default"
        assert doc.workspace_id == ""
        assert doc.metadata == {}

    def test_custom_fields(self):
        doc = VectorDocument(
            id="1", text="test", workspace_id="ws1",
            collection="hooks", metadata={"score": 92},
        )
        assert doc.workspace_id == "ws1"
        assert doc.collection == "hooks"


class TestCosineSimlarity:
    def test_identical_vectors(self, store: VectorStore):
        vec = {"a": 0.5, "b": 0.5}
        assert store._cosine_similarity(vec, vec) == pytest.approx(1.0)

    def test_orthogonal_vectors(self, store: VectorStore):
        vec_a = {"a": 1.0}
        vec_b = {"b": 1.0}
        assert store._cosine_similarity(vec_a, vec_b) == pytest.approx(0.0, abs=1e-6)
