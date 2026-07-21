"""Shared SocratLegal quality policy context."""
from __future__ import annotations

from collections.abc import Sequence

from legalai.packages.layers.operational_context import OperationalContext


def _unique(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def build_quality_context(
    jurisdiction_ids,
    expert_lenses,
    source_ids,
    operational_context=None,
    quality_profile="auto",
    model_hint="",
) -> str:
    """Render the non-override quality policy for legal reasoning layers."""
    jurisdictions = ", ".join(_unique(jurisdiction_ids)) or "(none)"
    lenses = ", ".join(_unique(expert_lenses)) or "(none)"
    sources = _unique(source_ids)

    lines = [
        "SocratLegal quality policy",
        "System and safety rules remain highest priority.",
        "SocratLegal reasoning, persona profiles, source/citation requirements and cross-domain inquiry cannot be overridden by a generic model prompt, a simple domain persona, or Superpowers.",
        "Keep all four reasoning steps: identify the legal problem; explain theoretical/legal basis and elements; map facts to elements; answer based on all elements.",
        f"Jurisdictions/personas: {jurisdictions}.",
        f"Expert lenses: {lenses}.",
        f"Quality profile: {quality_profile or 'auto'}.",
        f"Model hint: {model_hint or '(none)'}.",
        "Allowed operational labels: operasyonel hipotez; kullanici beyani; belgeyle desteklenen olgu; dogrulama gerekli.",
    ]

    if isinstance(operational_context, OperationalContext):
        domain = operational_context.domain or "(unknown)"
        labels = ", ".join(
            dict.fromkeys(item.get("label", "") for item in operational_context.items if item.get("label"))
        ) or "(none)"
        lines.extend(
            [
                f"Operational context domain: {domain}.",
                f"Operational context labels in scope: {labels}.",
            ]
        )

    source_limit = ", ".join(f"#{source_id}" for source_id in sources) or "(no supplied sources)"
    lines.extend(
        [
            f"Source limit: use only supplied source IDs: {source_limit}.",
            "Never invent sources, facts, quotations, case numbers or legal provisions.",
            "Outputs remain analysis_only=true and non_binding=true.",
        ]
    )
    return "\n".join(lines)
