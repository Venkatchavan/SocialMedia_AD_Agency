"""export.packager — Package run outputs into a zip (excluding raw comments)."""

from __future__ import annotations

import zipfile
from pathlib import Path

from core.config import run_path
from core.logging import get_logger

_log = get_logger(__name__)

# Files that must NEVER be packaged
_EXCLUDED = {"raw_comments.json", "raw_comments.csv"}


def package_run(workspace_id: str, run_id: str) -> Path:
    """Create a zip of all run artifacts (excluding raw comments)."""
    rp = run_path(workspace_id, run_id)
    zip_path = rp / f"packaged_run_{run_id}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fp in rp.rglob("*"):
            if fp.is_file() and fp.name not in _EXCLUDED and fp != zip_path:
                arcname = fp.relative_to(rp)
                zf.write(fp, arcname)

    _log.info("Packaged run to %s", zip_path)
    return zip_path
