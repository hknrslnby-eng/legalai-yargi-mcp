"""Deterministic composition of jurisdiction and expert-lens instructions."""
from __future__ import annotations

from collections.abc import Sequence

from legalai.packages.jurisdictions.loader import load_profile
from legalai.packages.layers.related_law_selection import select_related_law_domains


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
        if profile.related_law_domains:
            lines.append(f"RELATED_LAW_PROFILE: {profile.related_law_domains}")
        if profile.comparative_lenses:
            lines.append(f"COMPARATIVE_LENSES: {', '.join(profile.comparative_lenses)}")

    if expert_lenses:
        lines.append(f"EXPERT_LENSES: {', '.join(dict.fromkeys(expert_lenses))}")
        lines.append("Apply each detected subfield specialist only to the facts and legal issues it covers.")
    if any(profile_id == "kvkk" for profile_id in unique_ids) or any(
        lens.casefold() in {"nis_1", "nis_2", "nis-1", "nis-2", "siber_guvenlik"}
        for lens in expert_lenses
    ):
        related = select_related_law_domains(
            question="",
            primary_domain=unique_ids[0],
            supporting_domains=unique_ids[1:],
            expert_lenses=expert_lenses,
        )
        lines.append(f"RELATED_LAW_SUPPORTING: {', '.join(related.supporting) or '(none detected without facts)'}")
        lines.append("RELATED_LAW_RULE: Conditional idare/ceza and other supporting domains require concrete factual linkage.")
    lines.extend(
        [
            "Separate legislation, judicial decisions, institution decisions, doctrine, and policy references.",
            "Show contrary views, temporal assumptions, limitation/deadline risks, forum possibilities, and alternative legal routes.",
        ]
    )
    return "\n".join(lines)
