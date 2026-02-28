"""Base exporter ABC and shared helpers for brief export formats.

All exporters follow a common interface:
    exporter.export(brief_data, output_path) → ExportResult
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExportResult:
    """Result of an export operation."""

    format: str
    output_path: str
    file_size_bytes: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    success: bool = True
    error: str = ""


class BaseExporter(ABC):
    """Abstract base for all brief exporters."""

    format_name: str = "base"

    @abstractmethod
    def export(self, brief_data: dict[str, Any], output_path: str) -> ExportResult:
        """Export brief data to the target format.

        Args:
            brief_data: Dictionary containing brief sections.
            output_path: File path (without extension) for output.

        Returns:
            ExportResult with path and metadata.
        """
        ...

    def _ensure_dir(self, path: str) -> Path:
        """Ensure parent directory exists."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def _safe_get(self, data: dict, key: str, default: Any = "") -> Any:
        """Safe dictionary access with default."""
        return data.get(key, default)


def get_available_formats() -> list[str]:
    """Return list of supported export format names."""
    return ["markdown", "json", "html", "pptx", "pdf"]
