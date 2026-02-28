"""Onboarding flow orchestrator — manages the 5-step onboarding sequence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import structlog

from app.onboarding.url_scanner import BrandProfile, URLScanner

logger = structlog.get_logger(__name__)


class OnboardingStep(str, Enum):
    """Steps in the onboarding flow."""

    SIGNUP = "signup"
    BRAND_SCAN = "brand_scan"
    BRAND_REVIEW = "brand_review"
    SOCIAL_CONNECT = "social_connect"
    FIRST_RUN = "first_run"


STEP_ORDER = list(OnboardingStep)


@dataclass
class OnboardingState:
    """Tracks progress through the onboarding flow."""

    workspace_id: str
    user_id: str
    current_step: OnboardingStep = OnboardingStep.SIGNUP
    completed_steps: list[OnboardingStep] = field(default_factory=list)
    brand_profile: BrandProfile | None = None
    connected_platforms: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    @property
    def is_complete(self) -> bool:
        """Check if all onboarding steps are done."""
        return len(self.completed_steps) == len(STEP_ORDER)

    @property
    def progress_pct(self) -> int:
        """Percentage of onboarding complete (0-100)."""
        return int(len(self.completed_steps) / len(STEP_ORDER) * 100)


class OnboardingOrchestrator:
    """Manages the self-serve onboarding flow."""

    def __init__(self) -> None:
        self._scanner = URLScanner()
        self._states: dict[str, OnboardingState] = {}

    def start(self, workspace_id: str, user_id: str) -> OnboardingState:
        """Initialize onboarding for a new workspace."""
        state = OnboardingState(workspace_id=workspace_id, user_id=user_id)
        self._states[workspace_id] = state
        logger.info("onboarding_started", workspace_id=workspace_id)
        return state

    def get_state(self, workspace_id: str) -> OnboardingState | None:
        """Get current onboarding state."""
        return self._states.get(workspace_id)

    def complete_step(
        self, workspace_id: str, step: OnboardingStep
    ) -> OnboardingState:
        """Mark a step as completed and advance."""
        state = self._states.get(workspace_id)
        if state is None:
            raise ValueError(f"No onboarding state for workspace {workspace_id}")

        if step not in state.completed_steps:
            state.completed_steps.append(step)

        # Advance to next step
        idx = STEP_ORDER.index(step)
        if idx + 1 < len(STEP_ORDER):
            state.current_step = STEP_ORDER[idx + 1]
        else:
            state.completed_at = datetime.utcnow()

        logger.info(
            "onboarding_step_complete",
            workspace_id=workspace_id,
            step=step.value,
            progress=state.progress_pct,
        )
        return state

    def scan_brand_url(self, workspace_id: str, url: str) -> BrandProfile:
        """Scan a brand URL and store the profile."""
        state = self._states.get(workspace_id)
        if state is None:
            raise ValueError(f"No onboarding state for workspace {workspace_id}")

        profile = self._scanner.scan(url)
        state.brand_profile = profile
        return profile

    def scan_brand_html(
        self, workspace_id: str, url: str, html: str
    ) -> BrandProfile:
        """Scan pre-fetched HTML for brand info."""
        state = self._states.get(workspace_id)
        if state is None:
            raise ValueError(f"No onboarding state for workspace {workspace_id}")

        profile = self._scanner.scan_html(url, html)
        state.brand_profile = profile
        return profile

    def connect_platform(self, workspace_id: str, platform: str) -> bool:
        """Record a social platform connection."""
        state = self._states.get(workspace_id)
        if state is None:
            return False

        if platform not in state.connected_platforms:
            state.connected_platforms.append(platform)

        logger.info(
            "platform_connected",
            workspace_id=workspace_id,
            platform=platform,
        )
        return True
