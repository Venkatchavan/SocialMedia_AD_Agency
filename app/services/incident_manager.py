"""Incident management service.

Handles creation, tracking, and alerting for security and compliance incidents.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog

from app.schemas.incident import Incident
from app.services.audit_logger import AuditLogger

logger = structlog.get_logger(__name__)


class IncidentManager:
    """Create and manage incidents for compliance violations, security events, etc."""

    def __init__(self, audit_logger: AuditLogger) -> None:
        self._audit = audit_logger
        self._incidents: list[Incident] = []

    def create_incident(
        self,
        incident_type: str,
        description: str,
        severity: str = "medium",
        affected_posts: list[str] | None = None,
        affected_platforms: list[str] | None = None,
        created_by: str = "system",
    ) -> Incident:
        """Create a new incident and log it.

        Args:
            incident_type: Type of incident (dmca, policy_violation, token_leak, etc.)
            description: Detailed description.
            severity: low | medium | high | critical
            affected_posts: List of affected post IDs.
            affected_platforms: List of affected platform names.
            created_by: Who created this incident.

        Returns:
            The created Incident.
        """
        incident = Incident(
            id=str(uuid.uuid4()),
            incident_type=incident_type,
            severity=severity,
            description=description,
            affected_posts=affected_posts or [],
            affected_platforms=affected_platforms or [],
            status="open",
            created_at=datetime.now(tz=UTC),
            created_by=created_by,
        )

        self._incidents.append(incident)

        # Log to audit trail
        self._audit.log(
            agent_id="incident_manager",
            action="create_incident",
            decision="INCIDENT",
            reason=description,
            input_data={
                "type": incident_type,
                "severity": severity,
                "affected_posts": affected_posts or [],
            },
            metadata={"incident_id": incident.id},
        )

        logger.warning(
            "incident_created",
            incident_id=incident.id,
            type=incident_type,
            severity=severity,
        )

        return incident

    def resolve_incident(
        self, incident_id: str, resolution: str, resolved_by: str = "system"
    ) -> Incident | None:
        """Resolve an open incident."""
        for incident in self._incidents:
            if incident.id == incident_id and incident.status == "open":
                incident.status = "resolved"
                incident.resolution = resolution
                incident.resolved_at = datetime.now(tz=UTC)

                self._audit.log(
                    agent_id="incident_manager",
                    action="resolve_incident",
                    decision="RESOLVED",
                    reason=resolution,
                    metadata={
                        "incident_id": incident_id,
                        "resolved_by": resolved_by,
                    },
                )

                logger.info(
                    "incident_resolved",
                    incident_id=incident_id,
                    resolution=resolution,
                )
                return incident
        return None

    def get_open_incidents(self) -> list[Incident]:
        """Get all open incidents."""
        return [i for i in self._incidents if i.status == "open"]

    def get_incidents_by_type(self, incident_type: str) -> list[Incident]:
        """Get all incidents of a specific type."""
        return [i for i in self._incidents if i.incident_type == incident_type]
