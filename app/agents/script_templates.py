"""Script templates and scene generators for the Scriptwriter Agent.

Extracted to keep scriptwriter.py under the 250-line limit.
"""
from __future__ import annotations

from app.schemas.content import ScriptScene

# Script templates by content angle
SCRIPT_TEMPLATES: dict[str, dict] = {
    "comparison": {
        "hook_templates": [
            "Everyone says {product_a} is the best, but wait till you see this...",
            "{product_a} vs the alternative — here's what nobody tells you",
        ],
        "scene_count": 4,
        "duration_target": 30,
    },
    "top_3": {
        "hook_templates": [
            "3 things I wish I knew before buying {category}...",
            "Stop scrolling — here are the top 3 {category} picks",
        ],
        "scene_count": 5,
        "duration_target": 45,
    },
    "story": {
        "hook_templates": [
            "I was about to give up on {use_case} until I found this...",
            "This changed everything about my {use_case} routine",
        ],
        "scene_count": 4,
        "duration_target": 45,
    },
    "problem_solution": {
        "hook_templates": [
            "Struggling with {problem}? Here's what actually works.",
            "If {problem} is ruining your day, you need to see this",
        ],
        "scene_count": 4,
        "duration_target": 30,
    },
    "aesthetic": {
        "hook_templates": [
            "POV: Your {use_case} setup hits different ✨",
            "The aesthetic {use_case} setup you didn't know you needed",
        ],
        "scene_count": 3,
        "duration_target": 20,
    },
    "meme_style": {
        "hook_templates": [
            "Me pretending I don't need {product} vs. me at 3am adding it to cart",
            "Nobody: ... Me: *adds {product} to cart for the 5th time*",
        ],
        "scene_count": 3,
        "duration_target": 15,
    },
}


def build_template_scenes(
    angle: str,
    template: dict,
    product_title: str,
    use_cases: list[str],
    reference_style: str,
) -> list[ScriptScene]:
    """Generate body scenes from templates (deterministic fallback)."""
    scene_count = template.get("scene_count", 3)
    scenes: list[ScriptScene] = []

    if angle == "problem_solution":
        vis1 = (f"Show frustration scene. {reference_style}"
                if reference_style else "Show frustration with alternatives")
        vis2 = (f"Product reveal shot. {reference_style}"
                if reference_style else "Clean product reveal")
        scenes = [
            ScriptScene(scene_number=1, scene_type="problem",
                        dialogue=f"Finding the right {product_title} can be overwhelming.",
                        visual_direction=vis1, duration_seconds=5),
            ScriptScene(scene_number=2, scene_type="solution_reveal",
                        dialogue=f"That's why {product_title} stands out from the rest.",
                        visual_direction=vis2, duration_seconds=5),
            ScriptScene(scene_number=3, scene_type="demo",
                        dialogue=f"Perfect for {', '.join(use_cases[:2])}.",
                        visual_direction="Lifestyle usage demonstration", duration_seconds=8),
            ScriptScene(scene_number=4, scene_type="social_proof",
                        dialogue="See why people are switching.",
                        visual_direction="Show product features and benefits", duration_seconds=5),
        ]
    elif angle == "aesthetic":
        vis1 = (f"Cinematic product shot. {reference_style}"
                if reference_style else "Beautiful flat lay arrangement")
        vis2 = (f"Lifestyle scene. {reference_style}"
                if reference_style else "Person using product in stylish environment")
        scenes = [
            ScriptScene(scene_number=1, scene_type="aesthetic_showcase", dialogue="",
                        visual_direction=vis1, duration_seconds=6),
            ScriptScene(scene_number=2, scene_type="lifestyle",
                        dialogue=f"Elevate your {use_cases[0] if use_cases else 'daily'} setup.",
                        visual_direction=vis2, duration_seconds=7),
            ScriptScene(scene_number=3, scene_type="detail",
                        dialogue="The details make the difference.",
                        visual_direction="Close-up product details", duration_seconds=5),
        ]
    else:
        for i in range(min(scene_count, 4)):
            scenes.append(
                ScriptScene(scene_number=i + 1, scene_type="body",
                            dialogue=f"Feature {i + 1} of {product_title}.",
                            visual_direction=f"Demonstrate feature {i + 1}",
                            duration_seconds=5)
            )

    return scenes[:scene_count]
