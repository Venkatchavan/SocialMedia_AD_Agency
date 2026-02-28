"""collectors.base — Abstract collector interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.enums import Platform
from core.schemas_asset import Asset


class BaseCollector(ABC):
    """All platform collectors extend this."""

    platform: Platform

    @abstractmethod
    def collect(
        self,
        workspace_id: str,
        run_id: str,
        brand: str,
        **kwargs,
    ) -> list[Asset]:
        """Run collection and return normalised Asset list."""
        ...

    def name(self) -> str:
        return self.__class__.__name__

    def version(self) -> str:
        return "0.1.0"
