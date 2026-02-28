"""White-labeling support (U-17).

Custom domain, logo, colors, email templates per workspace.
Removes all default branding in client-facing views and exports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class WhiteLabelConfig:
    """White-label branding configuration per workspace."""

    workspace_id: str
    agency_name: str = ""
    logo_url: str = ""
    favicon_url: str = ""
    primary_color: str = "#4A90D9"
    secondary_color: str = "#2C3E50"
    accent_color: str = "#E74C3C"
    font_family: str = "Inter, sans-serif"
    custom_domain: str = ""  # e.g., "dashboard.myagency.com"
    email_from_name: str = ""
    email_from_address: str = ""
    footer_text: str = ""
    custom_css: str = ""

    def has_custom_branding(self) -> bool:
        """Check if any custom branding is configured."""
        return bool(self.agency_name or self.logo_url or self.custom_domain)


class WhiteLabelRegistry:
    """Manages white-label configs across workspaces."""

    def __init__(self) -> None:
        self._configs: dict[str, WhiteLabelConfig] = {}

    def set_config(self, config: WhiteLabelConfig) -> None:
        """Store a white-label config for a workspace."""
        self._configs[config.workspace_id] = config
        logger.info(
            "white_label_set",
            workspace_id=config.workspace_id,
            agency_name=config.agency_name,
        )

    def get_config(self, workspace_id: str) -> WhiteLabelConfig:
        """Get white-label config. Returns default if not configured."""
        return self._configs.get(
            workspace_id,
            WhiteLabelConfig(workspace_id=workspace_id),
        )

    def has_config(self, workspace_id: str) -> bool:
        """Check if workspace has custom branding."""
        return workspace_id in self._configs

    def apply_to_export(
        self, workspace_id: str, export_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply white-label branding to export data."""
        config = self.get_config(workspace_id)
        branded = dict(export_data)

        if config.agency_name:
            branded["branding"] = {
                "name": config.agency_name,
                "logo_url": config.logo_url,
                "primary_color": config.primary_color,
                "secondary_color": config.secondary_color,
                "font_family": config.font_family,
            }
            # Replace default branding
            if "footer" in branded:
                branded["footer"] = branded["footer"].replace(
                    "Creative Intelligence OS", config.agency_name
                )
        return branded

    def get_css_overrides(self, workspace_id: str) -> str:
        """Generate CSS overrides for the dashboard."""
        config = self.get_config(workspace_id)
        parts = [
            f":root {{",
            f"  --primary: {config.primary_color};",
            f"  --secondary: {config.secondary_color};",
            f"  --accent: {config.accent_color};",
            f"  --font: {config.font_family};",
            f"}}",
        ]
        if config.custom_css:
            parts.append(config.custom_css)
        return "\n".join(parts)

    def remove_config(self, workspace_id: str) -> bool:
        """Remove white-label config for a workspace."""
        if workspace_id in self._configs:
            del self._configs[workspace_id]
            return True
        return False
