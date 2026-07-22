"""Ortak Pipeline iskeleti. Bkz. FORK-KAPSAMLI-PLAN.md §6."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence

from legalai.packages.shared.types import Document


@dataclass
class Context:
    tenant_id: str
    question: str
    mode: str                                  # standard | deep | opposing | layered
    jurisdiction_id: str | None = None
    jurisdiction_scores: dict[str, int] = field(default_factory=dict)   # QualifyIssue teşhis çıktısı
    jurisdiction_ids: list[str] = field(default_factory=list)
    expert_lenses: list[str] = field(default_factory=list)
    jurisdiction_confidence: float = 0.0
    documents: list[Document] = field(default_factory=list)
    scored: list[Any] = field(default_factory=list)
    ratios: list[Any] = field(default_factory=list)
    dictums: list[Any] = field(default_factory=list)
    dissents: list[Any] = field(default_factory=list)
    counter_args: list[Any] = field(default_factory=list)
    argument_scores: list[Any] = field(default_factory=list)   # ArgumentStrengthScorer çıktısı
    answer: str | None = None
    citations: list[Any] = field(default_factory=list)
    citation_retry_hint: str | None = None   # VerifiedCitationCheck'in yeniden deneme talimatı
    trace: list[dict[str, Any]] = field(default_factory=list)   # her katman ne yaptı
    temporal_context: Any | None = None
    evidence: list[Any] = field(default_factory=list)
    strategy_options: list[Any] = field(default_factory=list)
    forum_candidates: list[Any] = field(default_factory=list)
    output_contract: str | None = None
    quality_profile: str = "auto"
    model_hint: str = ""
    source_query_plan: Any | None = None
    source_availability: dict[str, str] = field(default_factory=dict)
    source_errors: list[dict[str, Any]] = field(default_factory=list)
    missing_facts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        plan = self.source_query_plan
        return {
            "tenant_id": self.tenant_id,
            "question": self.question,
            "mode": self.mode,
            "jurisdiction_ids": list(self.jurisdiction_ids),
            "expert_lenses": list(self.expert_lenses),
            "source_query_plan": plan.to_dict() if hasattr(plan, "to_dict") else plan,
            "source_availability": dict(self.source_availability),
            "source_errors": list(self.source_errors),
            "missing_facts": list(self.missing_facts),
        }


class Layer(Protocol):
    name: str

    async def run(self, ctx: Context) -> Context: ...


@dataclass
class Pipeline:
    layers: Sequence[Layer]

    async def run(self, ctx: Context) -> Context:
        for layer in self.layers:
            t0 = time.perf_counter()
            ctx = await layer.run(ctx)
            ctx.trace.append({"layer": layer.name, "ms": (time.perf_counter() - t0) * 1000})
        return ctx
