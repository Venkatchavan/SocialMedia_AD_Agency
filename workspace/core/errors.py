"""core.errors — Custom exception hierarchy."""

from __future__ import annotations


class CreativeOSError(Exception):
    """Base exception for all Creative Intelligence OS errors."""


class ConfigError(CreativeOSError):
    """Invalid or missing configuration."""


class CollectionError(CreativeOSError):
    """Failure during ad collection."""


class AnalysisError(CreativeOSError):
    """Failure during media / comment analysis."""


class SynthesisError(CreativeOSError):
    """Failure during clustering / insight synthesis."""


class BriefError(CreativeOSError):
    """Failure during brief generation."""


class QAFailError(CreativeOSError):
    """QA gate reported a hard FAIL — export blocked."""


class ExportError(CreativeOSError):
    """Failure during export / packaging."""


class SSRFError(CreativeOSError):
    """Blocked request — potential SSRF attempt."""


class URLNotAllowedError(CreativeOSError):
    """URL does not match the allowlist."""
