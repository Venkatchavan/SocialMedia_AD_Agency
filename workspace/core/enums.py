"""core.enums — Deterministic enum definitions for the Creative Intelligence OS."""

from enum import Enum


class Platform(str, Enum):
    META = "meta"
    TIKTOK = "tiktok"
    X = "x"
    PINTEREST = "pinterest"


class AssetStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"


class AssetType(str, Enum):
    VIDEO = "video"
    IMAGE = "image"
    CAROUSEL = "carousel"
    UNKNOWN = "unknown"


class FormatType(str, Enum):
    UGC_SELFIE = "ugc_selfie"
    DEMO = "demo"
    TESTIMONIAL = "testimonial"
    FOUNDER = "founder"
    ANIMATION = "animation"
    MEME = "meme"
    OTHER = "other"
    UNKNOWN = "unknown"


class HookTactic(str, Enum):
    PATTERN_INTERRUPT = "pattern_interrupt"
    CURIOSITY_GAP = "curiosity_gap"
    RESULTS_FIRST = "results_first"
    MYTH_BUST = "myth_bust"
    PROBLEM_SOLUTION = "problem_solution"
    OTHER = "other"


class MessagingAngle(str, Enum):
    PAIN_RELIEF = "pain_relief"
    CONVENIENCE = "convenience"
    STATUS = "status"
    SCIENCE = "science"
    VALUE = "value"
    IDENTITY = "identity"
    OTHER = "other"


class OfferType(str, Enum):
    PERCENT_OFF = "percent_off"
    BUNDLE = "bundle"
    FREE_GIFT = "free_gift"
    TRIAL = "trial"
    GUARANTEE = "guarantee"
    SUBSCRIBE_SAVE = "subscribe_save"
    NONE = "none"
    UNKNOWN = "unknown"


class ProofElement(str, Enum):
    DEMO = "demo"
    SOCIAL_PROOF = "social_proof"
    AUTHORITY = "authority"
    BEFORE_AFTER = "before_after"
    STATS = "stats"
    GUARANTEE = "guarantee"
    NONE = "none"


class CTAType(str, Enum):
    SHOP_NOW = "shop_now"
    LEARN_MORE = "learn_more"
    SUBSCRIBE = "subscribe"
    DOWNLOAD = "download"
    OTHER = "other"
    UNKNOWN = "unknown"


class RiskFlag(str, Enum):
    COPYRIGHT = "copyright"
    MEDICAL_CLAIM = "medical_claim"
    FINANCIAL_CLAIM = "financial_claim"
    UNSAFE_CLAIM = "unsafe_claim"
    NONE = "none"


class AoTType(str, Enum):
    EVIDENCE = "EVIDENCE"
    TAG = "TAG"
    HYPOTHESIS = "HYPOTHESIS"
    DECISION = "DECISION"
    TEST = "TEST"


class Confidence(str, Enum):
    LOW = "low"
    MED = "med"
    HIGH = "high"


class QAResult(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class RiskLevel(str, Enum):
    LOW = "low"
    MED = "med"
    HIGH = "high"


class AgentStatus(str, Enum):
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"
