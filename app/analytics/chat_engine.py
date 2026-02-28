"""AI chat over analytics data (U-30).

RAG over run history, metrics, insights, brief outputs.
Uses LLM Router + vector store (U-10).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ChatMessage:
    """A single chat message."""

    role: str  # user, assistant, system
    content: str
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()


@dataclass
class ChatResponse:
    """Response from the analytics chat."""

    answer: str
    sources: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    query: str = ""


class AnalyticsChatEngine:
    """AI chat assistant over analytics and growth data.

    In production, this:
    1. Embeds the user query
    2. Searches vector store for relevant context (U-10)
    3. Builds RAG prompt with retrieved context
    4. Calls LLM Router for answer
    """

    def __init__(self, workspace_id: str) -> None:
        self.workspace_id = workspace_id
        self._history: list[ChatMessage] = []
        self._knowledge_base: list[dict[str, Any]] = []

    def add_knowledge(
        self,
        text: str,
        source_type: str = "metric",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a piece of knowledge to the RAG context."""
        self._knowledge_base.append({
            "text": text,
            "source_type": source_type,
            "metadata": metadata or {},
        })

    def ask(self, query: str) -> ChatResponse:
        """Ask a question about analytics data."""
        self._history.append(ChatMessage(role="user", content=query))

        # Retrieve relevant context (simple keyword matching; prod uses vector search)
        relevant = self._retrieve(query)

        # Generate answer (template-based; prod uses LLM)
        answer = self._generate_answer(query, relevant)

        response = ChatResponse(
            answer=answer,
            sources=relevant,
            confidence=min(1.0, len(relevant) * 0.2) if relevant else 0.1,
            query=query,
        )

        self._history.append(ChatMessage(
            role="assistant",
            content=answer,
            metadata={"sources_count": len(relevant)},
        ))

        logger.info(
            "chat_query",
            workspace_id=self.workspace_id,
            query_len=len(query),
            sources_found=len(relevant),
        )
        return response

    def get_history(self) -> list[ChatMessage]:
        """Get conversation history."""
        return list(self._history)

    def clear_history(self) -> None:
        """Clear conversation history."""
        self._history.clear()

    def _retrieve(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Simple keyword-based retrieval (prod: vector similarity)."""
        query_tokens = set(query.lower().split())
        scored: list[tuple[float, dict[str, Any]]] = []

        for doc in self._knowledge_base:
            doc_tokens = set(doc["text"].lower().split())
            overlap = len(query_tokens & doc_tokens)
            if overlap > 0:
                score = overlap / max(len(query_tokens), 1)
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:limit]]

    def _generate_answer(
        self, query: str, context: list[dict[str, Any]]
    ) -> str:
        """Generate answer from query + context (prod: LLM call)."""
        if not context:
            return (
                "I don't have enough data to answer that yet. "
                "Try running more campaigns to build up analytics."
            )

        # Build a summary from context
        summaries = [doc["text"] for doc in context[:3]]
        context_text = " | ".join(summaries)

        return (
            f"Based on your data: {context_text}. "
            f"This analysis covers {len(context)} relevant data points."
        )
