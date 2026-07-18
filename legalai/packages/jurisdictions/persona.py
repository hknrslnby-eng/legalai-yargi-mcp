"""Deterministic composition of jurisdiction and expert-lens instructions."""
from __future__ import annotations

from collections.abc import Sequence

from legalai.packages.jurisdictions.loader import load_profile


def compose_persona_instructions(
    profile_ids: Sequence[str],
    expert_lenses: Sequence[str] = (),
) -> str:
    """Compose a stable primary/supporting persona block for an LLM prompt."""
    unique_ids = list(dict.fromkeys(profile_ids))
    if not unique_ids:
        unique_ids = ["diger"]

    lines = [
        "LEGALAI PERSONA COMPOSITION",
        "Treat every role below as an expertise lens, not as a real identity claim.",
        "Keep the output analysis_only and non-binding; cite authority and uncertainty.",
    ]
    for index, profile_id in enumerate(unique_ids):
        profile = load_profile(profile_id)
        label = "PRIMARY_PROFILE" if index == 0 else "SUPPORTING_PROFILE"
        lines.extend([f"{label}: {profile.id}", f"PROFILE: {profile.id} — {profile.name}"])
        if profile.system_prompt_persona:
            lines.append(profile.system_prompt_persona.strip())
        if profile.response_tone:
            lines.append(f"Response tone: {profile.response_tone}")
        if profile.analysis_focus:
            lines.append(f"Analysis focus: {', '.join(profile.analysis_focus)}")

    if expert_lenses:
        lines.append(f"EXPERT_LENSES: {', '.join(dict.fromkeys(expert_lenses))}")
        lines.append("Apply each detected subfield specialist only to the facts and legal issues it covers.")
    lines.extend(
        [
            "Separate legislation, judicial decisions, institution decisions, doctrine, and policy references.",
            "Show contrary views, temporal assumptions, limitation/deadline risks, forum possibilities, and alternative legal routes.",
        ]
    )
    return "\n".join(lines)
