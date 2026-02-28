"""Tests for schema versioning (U-14)."""

from __future__ import annotations

from typing import Any

import pytest

from app.core.schema_versioning import (
    SchemaRegistry,
    SchemaVersionError,
)


def _migrate_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
    """Example: add 'display_name' from 'title'."""
    data["display_name"] = data.get("title", "Untitled")
    return data


def _migrate_v2_to_v3(data: dict[str, Any]) -> dict[str, Any]:
    """Example: normalize 'tags' field."""
    raw_tags = data.get("tags", "")
    if isinstance(raw_tags, str):
        data["tags"] = [t.strip() for t in raw_tags.split(",") if t.strip()]
    return data


@pytest.fixture
def registry() -> SchemaRegistry:
    """Schema registry at version 3 with two migrations."""
    reg = SchemaRegistry("product", current_version=3)
    reg.register_migration(1, 2, _migrate_v1_to_v2)
    reg.register_migration(2, 3, _migrate_v2_to_v3)
    return reg


# ── Registry Basics ───────────────────────────────────


class TestSchemaRegistry:
    def test_name_and_version(self, registry: SchemaRegistry) -> None:
        assert registry.name == "product"
        assert registry.current_version == 3

    def test_stamp_adds_version(self) -> None:
        reg = SchemaRegistry("test", current_version=2)
        stamped = reg.stamp({"title": "Hello"})
        assert stamped["schema_version"] == 2
        assert stamped["title"] == "Hello"

    def test_stamp_does_not_mutate_original(self) -> None:
        reg = SchemaRegistry("test", current_version=2)
        original = {"title": "Hello"}
        reg.stamp(original)
        assert "schema_version" not in original


class TestRegisterMigration:
    def test_non_sequential_raises(self) -> None:
        reg = SchemaRegistry("test", current_version=3)
        with pytest.raises(SchemaVersionError, match="sequential"):
            reg.register_migration(1, 3, lambda d: d)

    def test_valid_registration(self) -> None:
        reg = SchemaRegistry("test", current_version=2)
        reg.register_migration(1, 2, lambda d: d)  # no exception


# ── Load and Migrate ──────────────────────────────────


class TestLoadAndMigrate:
    def test_migrate_v1_to_v3(self, registry: SchemaRegistry) -> None:
        data = {"schema_version": 1, "title": "Widget", "tags": "a, b, c"}
        result = registry.load_and_migrate(data)
        assert result["schema_version"] == 3
        assert result["display_name"] == "Widget"
        assert result["tags"] == ["a", "b", "c"]

    def test_migrate_v2_to_v3(self, registry: SchemaRegistry) -> None:
        data = {"schema_version": 2, "display_name": "X", "tags": "x,y"}
        result = registry.load_and_migrate(data)
        assert result["schema_version"] == 3
        assert result["tags"] == ["x", "y"]

    def test_already_current_no_change(self, registry: SchemaRegistry) -> None:
        data = {"schema_version": 3, "display_name": "X", "tags": ["a"]}
        result = registry.load_and_migrate(data)
        assert result == data

    def test_no_version_defaults_to_1(self, registry: SchemaRegistry) -> None:
        data = {"title": "Old"}
        result = registry.load_and_migrate(data)
        assert result["schema_version"] == 3
        assert result["display_name"] == "Old"

    def test_future_version_raises(self, registry: SchemaRegistry) -> None:
        with pytest.raises(SchemaVersionError, match="newer"):
            registry.load_and_migrate({"schema_version": 99})

    def test_invalid_version_raises(self, registry: SchemaRegistry) -> None:
        with pytest.raises(SchemaVersionError, match="Invalid"):
            registry.load_and_migrate({"schema_version": -1})

    def test_missing_migration_raises(self) -> None:
        reg = SchemaRegistry("test", current_version=3)
        reg.register_migration(1, 2, lambda d: d)
        # Missing v2→v3 migration
        with pytest.raises(SchemaVersionError, match="No migration"):
            reg.load_and_migrate({"schema_version": 1})

    def test_does_not_mutate_input(self, registry: SchemaRegistry) -> None:
        original = {"schema_version": 1, "title": "Keep"}
        registry.load_and_migrate(original)
        assert "display_name" not in original
        assert original["schema_version"] == 1
