"""Source classification and context policy loader."""
from __future__ import annotations

import pathlib
from dataclasses import dataclass

import yaml


CONFIGS_DIR = pathlib.Path(__file__).resolve().parents[2] / "configs" / "sources"


@dataclass(frozen=True)
class SourcePolicy:
    source_id: str
    label: str
    source_kind: str
    authority_level: str
    allowed_contexts: tuple[str, ...]
    full_text_storage: str
    citation_required: bool = True


def load_source_policies() -> dict[str, SourcePolicy]:
    policies: dict[str, SourcePolicy] = {}
    for path in sorted(CONFIGS_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for item in data.get("sources", []):
            policy = SourcePolicy(
                source_id=item["source_id"],
                label=item["label"],
                source_kind=item["source_kind"],
                authority_level=item["authority_level"],
                allowed_contexts=tuple(item.get("allowed_contexts", [])),
                full_text_storage=item.get("full_text_storage", "metadata_or_excerpt_only"),
                citation_required=bool(item.get("citation_required", True)),
            )
            policies[policy.source_id] = policy
    return policies


def policies_for_context(context: str) -> list[SourcePolicy]:
    return [
        policy
        for policy in load_source_policies().values()
        if context in policy.allowed_contexts
    ]
