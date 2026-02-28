"""12-week growth calendar planner (U-19).

Auto-generates from brief data:
- Weekly content themes
- Platform-specific post schedule
- Hook rotation plan
- Offer cadence
- A/B test schedule
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class CalendarEntry:
    """A single entry in the growth calendar."""

    week: int
    day_of_week: int  # 0=Mon, 6=Sun
    platform: str
    content_type: str  # "post" | "reel" | "story" | "pin" | "tweet"
    theme: str = ""
    hook_type: str = ""
    offer: str = ""
    ab_test: str = ""
    notes: str = ""


@dataclass
class WeekPlan:
    """Plan for a single week."""

    week_number: int
    theme: str
    entries: list[CalendarEntry] = field(default_factory=list)
    focus_platforms: list[str] = field(default_factory=list)


@dataclass
class GrowthCalendar:
    """Complete 12-week growth calendar."""

    workspace_id: str
    weeks: list[WeekPlan] = field(default_factory=list)
    start_date: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def total_entries(self) -> int:
        return sum(len(w.entries) for w in self.weeks)


# Rotating themes for 12 weeks
_DEFAULT_THEMES = [
    "Brand Introduction",
    "Problem Awareness",
    "Social Proof",
    "Product Features",
    "Behind the Scenes",
    "User Stories",
    "Comparison & Value",
    "Seasonal/Trending",
    "FAQ & Objections",
    "Exclusive Offers",
    "Community Building",
    "Year-in-Review / Recap",
]

_HOOK_ROTATION = [
    "curiosity", "fear", "aspirational", "comparison",
    "story", "question", "statistic", "challenge",
]

_POST_DAYS = {
    "instagram": [0, 2, 4],  # Mon, Wed, Fri
    "tiktok": [1, 3, 5],     # Tue, Thu, Sat
    "x": [0, 1, 2, 3, 4],    # Weekdays
    "pinterest": [0, 3],     # Mon, Thu
    "linkedin": [1, 3],      # Tue, Thu
    "youtube": [4],           # Fri
}


class CalendarPlanner:
    """Generate 12-week growth calendars from brief data."""

    def generate(
        self,
        workspace_id: str,
        platforms: list[str] | None = None,
        hooks: list[str] | None = None,
        offers: list[str] | None = None,
        weeks: int = 12,
    ) -> GrowthCalendar:
        """Generate a complete growth calendar.

        Args:
            workspace_id: Target workspace.
            platforms: Active platforms (default: instagram, tiktok).
            hooks: Available hook types.
            offers: Scheduled offers/promos.
            weeks: Number of weeks (default: 12).
        """
        if platforms is None:
            platforms = ["instagram", "tiktok"]
        if hooks is None:
            hooks = list(_HOOK_ROTATION)
        if offers is None:
            offers = []

        calendar = GrowthCalendar(workspace_id=workspace_id)

        for week_num in range(1, weeks + 1):
            theme_idx = (week_num - 1) % len(_DEFAULT_THEMES)
            theme = _DEFAULT_THEMES[theme_idx]

            week_plan = WeekPlan(
                week_number=week_num,
                theme=theme,
                focus_platforms=platforms,
            )

            for platform in platforms:
                days = _POST_DAYS.get(platform, [0, 3])
                for day in days:
                    hook_idx = (week_num + day) % len(hooks)
                    entry = CalendarEntry(
                        week=week_num,
                        day_of_week=day,
                        platform=platform,
                        content_type=self._content_type_for(platform),
                        theme=theme,
                        hook_type=hooks[hook_idx],
                    )

                    # Add offer every 3 weeks if available
                    if offers and week_num % 3 == 0 and day == days[0]:
                        offer_idx = (week_num // 3 - 1) % len(offers)
                        entry.offer = offers[offer_idx]

                    # Add A/B test suggestion every 4 weeks
                    if week_num % 4 == 0 and day == days[0]:
                        entry.ab_test = f"Test hook: {hooks[hook_idx]} vs {hooks[(hook_idx + 1) % len(hooks)]}"

                    week_plan.entries.append(entry)

            calendar.weeks.append(week_plan)

        logger.info(
            "calendar_generated",
            workspace_id=workspace_id,
            weeks=weeks,
            total_entries=calendar.total_entries,
        )
        return calendar

    def _content_type_for(self, platform: str) -> str:
        """Return default content type per platform."""
        mapping = {
            "instagram": "reel",
            "tiktok": "video",
            "x": "tweet",
            "pinterest": "pin",
            "linkedin": "post",
            "youtube": "short",
        }
        return mapping.get(platform, "post")
