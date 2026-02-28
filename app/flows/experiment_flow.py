"""Experiment Flow — A/B testing and variant management.

MVP: Simple variant assignment and result tracking.
Production: Statistical significance testing, auto-winner selection.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from app.schemas.analytics import Experiment, ExperimentVariant, ExperimentResult
from app.services.audit_logger import AuditLogger

logger = structlog.get_logger(__name__)


class ExperimentFlow:
    """Manage A/B experiments for content variants."""

    def __init__(self, audit_logger: AuditLogger) -> None:
        self._audit = audit_logger
        self._experiments: dict[str, Experiment] = {}

    def create_experiment(
        self,
        name: str,
        variants: list[dict[str, Any]],
        traffic_split: list[float] | None = None,
    ) -> Experiment:
        """Create a new experiment with variants."""
        if not variants or len(variants) < 2:
            raise ValueError("Experiment must have at least 2 variants")

        if traffic_split is None:
            # Equal split
            traffic_split = [1.0 / len(variants)] * len(variants)

        if len(traffic_split) != len(variants):
            raise ValueError("Traffic split must match number of variants")

        if abs(sum(traffic_split) - 1.0) > 0.01:
            raise ValueError("Traffic split must sum to 1.0")

        exp_variants = []
        for i, v in enumerate(variants):
            exp_variants.append(
                ExperimentVariant(
                    variant_id=str(uuid.uuid4()),
                    name=v.get("name", f"variant_{i}"),
                    config=v.get("config", {}),
                    traffic_percentage=traffic_split[i],
                )
            )

        experiment = Experiment(
            experiment_id=str(uuid.uuid4()),
            name=name,
            variants=exp_variants,
            status="active",
            created_at=datetime.now(tz=timezone.utc),
        )

        self._experiments[experiment.experiment_id] = experiment

        self._audit.log(
            agent_id="experiment_flow",
            action="experiment_created",
            decision="CREATED",
            reason=f"Experiment '{name}' created with {len(variants)} variants",
        )

        logger.info(
            "experiment_created",
            experiment_id=experiment.experiment_id,
            name=name,
            variant_count=len(variants),
        )

        return experiment

    def assign_variant(self, experiment_id: str) -> ExperimentVariant:
        """Assign a variant based on traffic split."""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        if experiment.status != "active":
            raise ValueError(f"Experiment {experiment_id} is {experiment.status}")

        # Weighted random selection
        r = random.random()
        cumulative = 0.0
        for variant in experiment.variants:
            cumulative += variant.traffic_percentage
            if r <= cumulative:
                return variant

        return experiment.variants[-1]

    def record_result(
        self,
        experiment_id: str,
        variant_id: str,
        metric_name: str,
        metric_value: float,
    ) -> None:
        """Record a single metric result for a variant."""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        for variant in experiment.variants:
            if variant.variant_id == variant_id:
                if not hasattr(variant, "_results"):
                    variant._results = []
                # Store in variant config as simple accumulator
                results_key = f"_results_{metric_name}"
                existing = variant.config.get(results_key, [])
                existing.append(metric_value)
                variant.config[results_key] = existing
                return

        raise ValueError(f"Variant {variant_id} not found in experiment {experiment_id}")

    def get_experiment_summary(self, experiment_id: str) -> dict[str, Any]:
        """Get a summary of experiment results."""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        summary: dict[str, Any] = {
            "experiment_id": experiment_id,
            "name": experiment.name,
            "status": experiment.status,
            "variants": [],
        }

        for variant in experiment.variants:
            variant_summary: dict[str, Any] = {
                "variant_id": variant.variant_id,
                "name": variant.name,
                "traffic_percentage": variant.traffic_percentage,
                "metrics": {},
            }

            # Extract accumulated results
            for key, value in variant.config.items():
                if key.startswith("_results_") and isinstance(value, list):
                    metric_name = key.replace("_results_", "")
                    variant_summary["metrics"][metric_name] = {
                        "count": len(value),
                        "mean": sum(value) / len(value) if value else 0,
                        "total": sum(value),
                    }

            summary["variants"].append(variant_summary)

        return summary

    def conclude_experiment(
        self, experiment_id: str, winner_variant_id: str | None = None
    ) -> dict[str, Any]:
        """Conclude an experiment, optionally declaring a winner."""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        experiment.status = "completed"

        self._audit.log(
            agent_id="experiment_flow",
            action="experiment_concluded",
            decision="COMPLETED",
            reason=f"Experiment '{experiment.name}' concluded. Winner: {winner_variant_id or 'none'}",
        )

        return {
            "experiment_id": experiment_id,
            "status": "completed",
            "winner": winner_variant_id,
        }
