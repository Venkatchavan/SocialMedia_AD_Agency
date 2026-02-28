"""core.schemas_aot — Atom of Thought ledger models."""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field

from core.enums import AoTType, Confidence


class AoTAtom(BaseModel):
    atom_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: AoTType
    source_assets: list[str] = Field(default_factory=list)
    content: str  # 1-3 sentences
    confidence: Confidence = Confidence.LOW
    next_check: Optional[str] = None
