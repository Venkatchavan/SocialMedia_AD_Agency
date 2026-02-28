"""Schema versioning — sequential migrations for JSON data schemas.

Adds schema_version tracking and auto-migration on load.
Prevents silent data corruption from schema drift (U-14).
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

# Migration function type: takes data dict, returns migrated data dict
MigrationFn = Callable[[dict[str, Any]], dict[str, Any]]


class SchemaVersionError(Exception):
    """Raised when schema version is invalid or migration fails."""

    pass


class SchemaRegistry:
    """Registry of schema migrations for a specific document type.

    Usage:
        registry = SchemaRegistry("product")
        registry.register_migration(1, 2, migrate_v1_to_v2)
        registry.register_migration(2, 3, migrate_v2_to_v3)

        data = registry.load_and_migrate(raw_data)
        # data is now at latest version
    """

    def __init__(self, schema_name: str, current_version: int = 1) -> None:
        self._name = schema_name
        self._current_version = current_version
        self._migrations: dict[int, MigrationFn] = {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def current_version(self) -> int:
        return self._current_version

    def register_migration(
        self,
        from_version: int,
        to_version: int,
        migrate_fn: MigrationFn,
    ) -> None:
        """Register a migration from one version to the next.

        Args:
            from_version: Source version.
            to_version: Target version (must be from_version + 1).
            migrate_fn: Function that transforms the data dict.

        Raises:
            SchemaVersionError: If versions are invalid.
        """
        if to_version != from_version + 1:
            raise SchemaVersionError(
                f"Migration must be sequential: "
                f"{from_version} → {to_version} (expected {from_version + 1})"
            )
        self._migrations[from_version] = migrate_fn

    def load_and_migrate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Load data and auto-migrate to the current version.

        Args:
            data: Raw data dict, optionally containing 'schema_version'.

        Returns:
            Migrated data with schema_version set to current_version.

        Raises:
            SchemaVersionError: If migration path is broken or data is invalid.
        """
        result = copy.deepcopy(data)
        version = result.get("schema_version", 1)

        if not isinstance(version, int) or version < 1:
            raise SchemaVersionError(
                f"Invalid schema_version: {version}"
            )

        if version > self._current_version:
            raise SchemaVersionError(
                f"Data version {version} is newer than current {self._current_version}"
            )

        while version < self._current_version:
            migrate_fn = self._migrations.get(version)
            if migrate_fn is None:
                raise SchemaVersionError(
                    f"No migration registered for {self._name} "
                    f"v{version} → v{version + 1}"
                )
            result = migrate_fn(result)
            version += 1

        result["schema_version"] = self._current_version
        return result

    def stamp(self, data: dict[str, Any]) -> dict[str, Any]:
        """Stamp data with the current schema version."""
        result = copy.deepcopy(data)
        result["schema_version"] = self._current_version
        return result
