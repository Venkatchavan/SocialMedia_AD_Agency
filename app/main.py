"""Main entry point — Wires all components and runs the pipeline.

Usage:
    python -m app.main --asin B0XXXXXXXXX --platforms tiktok,instagram
"""

from __future__ import annotations

import argparse
from typing import Any

import structlog

from app.agents.caption_seo import CaptionSEOAgent
from app.agents.manager import ManagerAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.product_enrichment import ProductEnrichmentAgent
from app.agents.product_intake import ProductIntakeAgent
from app.agents.reference_intelligence import ReferenceIntelligenceAgent
from app.agents.scriptwriter import ScriptwriterAgent
from app.config import get_settings
from app.flows.content_pipeline import ContentPipelineFlow
from app.flows.pipeline_state import PipelineState
from app.services.audit_logger import AuditLogger
from app.services.content_hasher import ContentHasher
from app.services.llm_client import LLMClient
from app.services.qa_checker import QAChecker
from app.services.rights_engine import RightsEngine
from app.services.risk_scorer import RiskScorer
from app.services.secrets import SecretsManager

logger = structlog.get_logger(__name__)


def build_pipeline() -> ContentPipelineFlow:
    """Wire all components and return a ready-to-run pipeline."""
    settings = get_settings()

    # Core services
    llm_client = LLMClient()
    audit_logger = AuditLogger()
    SecretsManager(backend=settings.secrets_backend)
    ContentHasher()
    rights_engine = RightsEngine(audit_logger=audit_logger)
    RiskScorer()
    qa_checker = QAChecker(audit_logger=audit_logger)

    # Agents (with LLM wiring)
    intake = ProductIntakeAgent(audit_logger=audit_logger)
    enrichment = ProductEnrichmentAgent(audit_logger=audit_logger, llm_client=llm_client)
    reference = ReferenceIntelligenceAgent(audit_logger=audit_logger)
    scriptwriter = ScriptwriterAgent(audit_logger=audit_logger, llm_client=llm_client)
    caption = CaptionSEOAgent(audit_logger=audit_logger, llm_client=llm_client)
    orchestrator = OrchestratorAgent(audit_logger=audit_logger)
    manager = ManagerAgent(audit_logger=audit_logger, llm_client=llm_client)

    # Wire the pipeline flow
    pipeline = ContentPipelineFlow(
        product_intake_agent=intake,
        product_enrichment_agent=enrichment,
        reference_intelligence_agent=reference,
        scriptwriter_agent=scriptwriter,
        caption_seo_agent=caption,
        orchestrator_agent=orchestrator,
        rights_engine=rights_engine,
        qa_checker=qa_checker,
        audit_logger=audit_logger,
        manager_agent=manager,
    )

    return pipeline


def run_pipeline(
    asin: str,
    platforms: list[str] | None = None,
    product_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the full content pipeline for a product.

    Args:
        asin: Amazon product ASIN.
        platforms: Target platforms (default: tiktok, instagram).
        product_data: Optional manual product data.

    Returns:
        Pipeline state as dict.
    """
    if platforms is None:
        platforms = ["tiktok", "instagram"]

    pipeline = build_pipeline()

    state = PipelineState(
        asin=asin,
        source="manual" if product_data else "api",
        target_platforms=platforms,
        product_data=product_data or {
            "asin": asin,
            "title": f"Product {asin}",
            "price": 29.99,
            "category": "Electronics",
        },
    )

    logger.info(
        "pipeline_run_started",
        asin=asin,
        platforms=platforms,
    )

    result_state = pipeline.run(state)

    logger.info(
        "pipeline_run_finished",
        asin=asin,
        status=result_state.status.value,
        pipeline_id=result_state.pipeline_id,
    )

    return result_state.model_dump(mode="json")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Affiliate Ad Agency — Content Pipeline",
    )
    parser.add_argument(
        "--asin",
        type=str,
        required=True,
        help="Amazon product ASIN (10 alphanumeric chars)",
    )
    parser.add_argument(
        "--platforms",
        type=str,
        default="tiktok,instagram",
        help="Comma-separated target platforms (default: tiktok,instagram)",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="",
        help="Product title (optional, for manual input)",
    )
    parser.add_argument(
        "--price",
        type=float,
        default=0.0,
        help="Product price (optional, for manual input)",
    )
    parser.add_argument(
        "--category",
        type=str,
        default="General",
        help="Product category (optional, for manual input)",
    )

    args = parser.parse_args()

    platforms = [p.strip() for p in args.platforms.split(",")]

    product_data: dict[str, Any] | None = None
    if args.title:
        product_data = {
            "asin": args.asin,
            "title": args.title,
            "price": args.price,
            "category": args.category,
        }

    result = run_pipeline(
        asin=args.asin,
        platforms=platforms,
        product_data=product_data,
    )

    # Print summary
    print(f"\n{'='*60}")
    print(f"Pipeline ID: {result.get('pipeline_id')}")
    print(f"Status:      {result.get('status')}")
    print(f"ASIN:        {result.get('asin')}")
    print(f"Platforms:   {', '.join(result.get('target_platforms', []))}")
    print(f"Rewrites:    {result.get('rewrite_count', 0)}")
    if result.get('error_message'):
        print(f"Error:       {result.get('error_message')}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
