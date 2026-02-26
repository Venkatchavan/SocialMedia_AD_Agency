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

    url = f"{_BASE}/acts/{actor_id}/runs"
    _log.info("Starting Apify actor %s", actor_id)
    with httpx.Client(timeout=timeout_secs) as client:
        resp = client.post(url, json=run_input, headers=_headers())
        resp.raise_for_status()
        run_data = resp.json()["data"]
        run_id = run_data["id"]
        dataset_id = run_data.get("defaultDatasetId", "")

        # Wait for finish
        wait_url = f"{_BASE}/actor-runs/{run_id}?waitForFinish={timeout_secs}"
        wait_resp = client.get(wait_url, headers=_headers())
        wait_resp.raise_for_status()

        # Fetch dataset items
        items_url = f"{_BASE}/datasets/{dataset_id}/items"
        items_resp = client.get(items_url, headers=_headers())
        items_resp.raise_for_status()
        items: list[dict[str, Any]] = items_resp.json()
    _log.info("Apify actor %s returned %d items", actor_id, len(items))
    return items
