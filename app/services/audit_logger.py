"""Immutable audit logging service with hash-chain tamper detection.

SECURITY: Audit events are append-only. No UPDATE or DELETE operations.
Every event includes a hash of the previous event for tamper detection.
Agents NEVER print secrets to audit logs.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime

import structlog

from app.schemas.audit import AuditEvent

logger = structlog.get_logger(__name__)


class AuditLogger:
    """Append-only audit logger with hash-chain integrity."""

    def __init__(
        self,
        store: object | None = None,
        session_factory: object | None = None,
    ) -> None:
        self._store = store  # Database / file store
        self._session_factory = session_factory  # SQLAlchemy sessionmaker
        self._last_event_hash: str = ""
        self._events: list[AuditEvent] = []  # In-memory fallback for dev

    def log(
        self,
        agent_id: str,
        action: str,
        decision: str = "",
        reason: str = "",
        input_data: dict | None = None,
        output_data: dict | None = None,
        session_id: str = "",
        metadata: dict | None = None,
    ) -> AuditEvent:
        """Create and persist an immutable audit event.

        Args:
            agent_id: Identifier of the agent/service creating the event.
            action: The action being audited (e.g., "verify_reference").
            decision: Decision outcome (APPROVE/REWRITE/REJECT/PUBLISH).
            reason: Human-readable explanation.
            input_data: Input data to hash (never stored raw if it contains secrets).
            output_data: Output data to hash.
            session_id: Pipeline run identifier for tracing.
            metadata: Additional context (must not contain secrets).

        Returns:
            The created AuditEvent.
        """
        # Hash inputs/outputs — never store raw sensitive data
        input_hash = self._hash_data(input_data) if input_data else ""
        output_hash = self._hash_data(output_data) if output_data else ""

        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            agent_id=agent_id,
            action=action,
            input_hash=input_hash,
            output_hash=output_hash,
            decision=decision,
            reason=reason,
            session_id=session_id,
            previous_event_hash=self._last_event_hash,
            metadata=metadata or {},
            created_at=datetime.now(tz=UTC),
        )

        # Update hash chain
        self._last_event_hash = self._hash_event(event)

        # Persist
        self._persist(event)

        logger.info(
            "audit_event_created",
            event_id=event.event_id,
            agent_id=agent_id,
            action=action,
            decision=decision,
        )

        return event

    def get_events(self, session_id: str = "") -> list[AuditEvent]:
        """Retrieve audit events, optionally filtered by session_id."""
        if session_id:
            return [e for e in self._events if e.session_id == session_id]
        return list(self._events)

    def verify_chain_integrity(self) -> bool:
        """Verify the hash chain has not been tampered with."""
        if not self._events:
            return True

        expected_prev_hash = ""
        for event in self._events:
            if event.previous_event_hash != expected_prev_hash:
                logger.error(
                    "audit_chain_tampered",
                    event_id=event.event_id,
                    expected=expected_prev_hash,
                    actual=event.previous_event_hash,
                )
                return False
            expected_prev_hash = self._hash_event(event)

        return True

    def _persist(self, event: AuditEvent) -> None:
        """Persist event to store. Append-only — never update or delete."""
        self._events.append(event)

        if self._session_factory is not None:
            self._persist_to_db(event)

    def _persist_to_db(self, event: AuditEvent) -> None:
        """Write audit event to database (append-only)."""
        try:
            from app.db.models import AuditEventModel

            session = self._session_factory()
            try:
                row = AuditEventModel(
                    id=event.event_id,
                    agent=event.agent_id,
                    action=event.action,
                    input_hash=event.input_hash,
                    output_hash=event.output_hash,
                    decision=event.decision,
                    reason=event.reason,
                    session_id=event.session_id,
                    previous_event_hash=event.previous_event_hash,
                    timestamp=event.created_at.isoformat(),
                    workspace_id="default",
                )
                session.add(row)
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        except Exception as e:
            logger.warning("audit_db_persist_failed", error=str(e))

    @staticmethod
    def _hash_data(data: dict) -> str:
        """SHA-256 hash of serialized data."""
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()

    @staticmethod
    def _hash_event(event: AuditEvent) -> str:
        """SHA-256 hash of the audit event for chain linking."""
        return hashlib.sha256(event.to_hash_input().encode()).hexdigest()
