"""collectors.apify_client — Thin wrapper around the Apify API."""

from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import APIFY_TOKEN
from core.errors import CollectionError
from core.logging import get_logger

_log = get_logger(__name__)
_BASE = "https://api.apify.com/v2"


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {APIFY_TOKEN}"}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def run_actor(
    actor_id: str,
    run_input: dict[str, Any],
    *,
    timeout_secs: int = 300,
) -> list[dict[str, Any]]:
    """Start an Apify actor run synchronously and return dataset items."""
    if not APIFY_TOKEN:
        raise CollectionError("APIFY_TOKEN is not set")

    actor_slug = actor_id.replace("/", "~")
    url = f"{_BASE}/acts/{actor_slug}/runs"
    _log.info("Starting Apify actor %s", actor_id)

    # Start the run (short timeout — just needs to create, not wait)
    resp = httpx.post(url, json=run_input, headers=_headers(), timeout=30)
    resp.raise_for_status()
    run_id = resp.json()["data"]["id"]

    # Poll for finish — add 30s buffer so httpx doesn't race Apify's long-poll
    wait_url = f"{_BASE}/actor-runs/{run_id}?waitForFinish={timeout_secs}"
    wait_resp = httpx.get(wait_url, headers=_headers(), timeout=timeout_secs + 30)
    wait_resp.raise_for_status()
    finished = wait_resp.json()["data"]
    status = finished.get("status", "")
    if status not in ("SUCCEEDED",):
        raise CollectionError(f"Apify actor run {run_id} ended with status={status}")
    dataset_id = finished.get("defaultDatasetId", "")
    if not dataset_id:
        raise CollectionError(f"Apify actor run {run_id} returned no dataset")

    # Fetch dataset items
    items_url = f"{_BASE}/datasets/{dataset_id}/items"
    items_resp = httpx.get(items_url, headers=_headers(), timeout=60)
    items_resp.raise_for_status()
    items: list[dict[str, Any]] = items_resp.json()
    _log.info("Apify actor %s returned %d items", actor_id, len(items))
    return items
    _log.info("Apify actor %s returned %d items", actor_id, len(items))
    return items
