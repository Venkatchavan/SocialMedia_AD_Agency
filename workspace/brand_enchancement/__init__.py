"""brand_enchancement — Incremental, versioned Brand Enhancement Engine.

Public surface:
    from brand_enchancement.engine import update_brand_bible
    from brand_enchancement.schemas import BrandBibleDoc, UpdateSignal
    from brand_enchancement.versioning import list_versions, load_version
"""

from brand_enchancement.engine import EnhanceResult, update_brand_bible
from brand_enchancement.schemas import BrandBibleDoc, UpdateSignal

__all__ = [
    "update_brand_bible",
    "EnhanceResult",
    "BrandBibleDoc",
    "UpdateSignal",
]
