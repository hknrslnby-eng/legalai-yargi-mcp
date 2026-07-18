"""JurisdictionProfile — YAML profil şemasının Python karşılığı.
Bkz. FORK-KAPSAMLI-PLAN.md §3.1, §3.2."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class JurisdictionProfile:
    id: str
    name: str
    version: int = 1
    axes: list[str] = field(default_factory=list)
    hierarchy: list[str] = field(default_factory=list)
    ratio_markers: list[str] = field(default_factory=list)
    dictum_markers: list[str] = field(default_factory=list)
    transfer_markers: list[str] = field(default_factory=list)
    dissent_headers: list[str] = field(default_factory=list)
    procedural_deadlines: dict[str, Any] = field(default_factory=dict)
    evidence_standard: str = ""
    system_prompt_persona: str = ""
    response_tone: str = ""
    disclaimer_required: bool = False
    expert_lenses: list[str] = field(default_factory=list)
    analysis_focus: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)   # ham YAML — override sınıfları için

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JurisdictionProfile":
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            version=data.get("version", 1),
            axes=list(data.get("axes", [])),
            hierarchy=list(data.get("hierarchy", [])),
            ratio_markers=list(data.get("ratio_markers", [])),
            dictum_markers=list(data.get("dictum_markers", [])),
            transfer_markers=list(data.get("transfer_markers", [])),
            dissent_headers=list(data.get("dissent_headers", [])),
            procedural_deadlines=dict(data.get("procedural_deadlines", {})),
            evidence_standard=data.get("evidence_standard", ""),
            system_prompt_persona=data.get("system_prompt_persona", ""),
            response_tone=data.get("response_tone", ""),
            disclaimer_required=bool(data.get("disclaimer_required", False)),
            expert_lenses=list(data.get("expert_lenses", [])),
            analysis_focus=list(data.get("analysis_focus", [])),
            raw=data,
        )
