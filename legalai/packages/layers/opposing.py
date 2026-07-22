"""Hafta 9 agresif karşı taraf, temporal bağlam ve strateji akışı."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Protocol

from legalai.packages.jurisdictions.base import JurisdictionProfile
from legalai.packages.jurisdictions.loader import JurisdictionNotFoundError, load_profile
from legalai.packages.jurisdictions.selection import guess_jurisdictions
from legalai.packages.layers.forum_analyzer import ForumAndDeadlineAnalyzer
from legalai.packages.jurisdictions.persona import compose_persona_instructions
from legalai.packages.layers.legal_reasoning import build_reasoning_instructions
from legalai.packages.layers.operational_context import OperationalContextBuilder
from legalai.packages.layers.legal_source_backend import IntegratedLegalSourceBackend
from legalai.packages.layers.strategy_planner import StrategicPath, StrategicPathPlanner
from legalai.packages.layers.temporal_context import (
    DeadlineRisk,
    LimitationAndPreclusionAnalyzer,
    TemporalLegalContextBuilder,
)
from legalai.packages.shared.evidence import EvidenceBlock, SourceScope, validate_source_scope
from legalai.packages.shared.settings import settings
from legalai.packages.shared.temporal import TemporalLegalContext


SUPPORTED_ROLES = frozenset(("davacı", "davalı", "sanık", "katılan", "başvurucu", "karşı_taraf", "idare"))


@dataclass
class RoleMapping:
    role: str
    position: str
    opposing_role: str
    inversion_questions: list[str]


@dataclass
class CounterArgument:
    title: str
    argument: str
    burden_or_risk: str
    response_focus: str
    confidence: float = 0.0


@dataclass
class WeakPoint:
    title: str
    description: str
    consequence: str
    confidence: float = 0.0


@dataclass
class OpposingResult:
    question: str
    mode: str
    role: str
    position: str
    counter_arguments: list[CounterArgument] = field(default_factory=list)
    rebutting_evidence: list[EvidenceBlock] = field(default_factory=list)
    weak_points: list[WeakPoint] = field(default_factory=list)
    temporal_context: TemporalLegalContext = field(default_factory=TemporalLegalContext)
    deadline_risks: list[DeadlineRisk] = field(default_factory=list)
    forum_candidates: list[Any] = field(default_factory=list)
    strategy_options: list[StrategicPath] = field(default_factory=list)
    evidence: list[EvidenceBlock] = field(default_factory=list)
    answer: str | None = None
    assistant_instructions: str | None = None
    analysis_only: bool = True
    non_binding: bool = True
    confidence: float = 0.0
    assumptions: list[str] = field(default_factory=list)
    missing_facts: list[str] = field(default_factory=list)
    source_scope: SourceScope = "targeted"
    operational_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "mode": self.mode,
            "role": self.role,
            "position": self.position,
            "counter_arguments": [item.__dict__ for item in self.counter_arguments],
            "rebutting_evidence": [item.to_dict() for item in self.rebutting_evidence],
            "weak_points": [item.__dict__ for item in self.weak_points],
            "temporal_context": _dataclass_dict(self.temporal_context),
            "deadline_risks": [_dataclass_dict(item) for item in self.deadline_risks],
            "forum_candidates": [_dataclass_dict(item) for item in self.forum_candidates],
            "strategy_options": [_dataclass_dict(item) for item in self.strategy_options],
            "evidence": [item.to_dict() for item in self.evidence],
            "answer": self.answer,
            "assistant_instructions": self.assistant_instructions,
            "analysis_only": True,
            "non_binding": True,
            "confidence": self.confidence,
            "assumptions": self.assumptions,
            "missing_facts": self.missing_facts,
            "source_scope": self.source_scope,
            "operational_context": self.operational_context,
        }


class LLMClient(Protocol):
    async def generate(self, system: str, user: str) -> str: ...


class RebuttingCaseSearch:
    """Karşı argümanları aynı karar backend'inde otomatik arar."""

    def __init__(self, backend: Any) -> None:
        self.backend = backend
        self.errors: list[str] = []

    async def search(
        self,
        counter_args: list[CounterArgument],
        source_scope: SourceScope,
        selected_source_ids: list[str] | None = None,
        limit: int = 3,
    ) -> list[EvidenceBlock]:
        del source_scope, selected_source_ids
        evidence: list[EvidenceBlock] = []
        for counter in counter_args:
            if len(evidence) >= limit:
                break
            try:
                documents = await self.backend.search(counter.argument, 1)
            except Exception as exc:
                self.errors.append(f"rebutting search failed: {type(exc).__name__}")
                continue
            for document in documents:
                body = str(getattr(document, "body", "")).strip()
                if not body:
                    continue
                evidence.append(
                    EvidenceBlock(
                        claim=f"Karşı argüman için aranan karşıt kaynak: {counter.title}",
                        source_type=str(getattr(document, "source", "document")),
                        citation_key=str(getattr(document, "id", "")),
                        full_citation=str(getattr(document, "citation", "")),
                        short_quote=body[:240],
                        source_url="",
                        document_id=str(getattr(document, "id", "")),
                        temporal_status="document-date-not-resolved",
                        relevance="medium",
                        confidence=0.35,
                    )
                )
                if len(evidence) >= limit:
                    break
        return evidence


def _dataclass_dict(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if hasattr(value, "__dict__"):
        return {key: _dataclass_dict(item) for key, item in value.__dict__.items()}
    if isinstance(value, list):
        return [_dataclass_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: _dataclass_dict(item) for key, item in value.items()}
    return value


def _role_mapping(position: str, role: str) -> RoleMapping:
    if role not in SUPPORTED_ROLES:
        raise ValueError(f"role must be one of: {', '.join(sorted(SUPPORTED_ROLES))}")
    opposites = {"davacı": "davalı", "davalı": "davacı", "sanık": "katılan", "katılan": "sanık", "başvurucu": "idare", "idare": "başvurucu", "karşı_taraf": "davacı"}
    opposing = opposites[role]
    return RoleMapping(
        role=role,
        position=position,
        opposing_role=opposing,
        inversion_questions=[
            "Karşı taraf bu vakıayı ve belgeyi hangi unsurdan çürütebilir?",
            "Görev, yetki, süre veya dava şartı itirazı var mı?",
            "Aynı delil aleyhe nasıl yorumlanabilir?",
        ],
    )


def _counter_arguments(position: str, role_mapping: RoleMapping) -> list[CounterArgument]:
    stems = [
        ("Vakıa ve ispat", "Olayın veya belgenin iddia edildiği biçimde gerçekleşmediği ileri sürülebilir.", "İspat yükü ve belge bütünlüğü", "Kronoloji, asli belge ve karşı delil matrisi"),
        ("Muacceliyet/unsur", "Talebin unsurları veya muacceliyet koşulu henüz oluşmamış olabilir.", "Talep şartlarının ispatı", "Sözleşme, ifa ve temerrüt tarihleri"),
        ("Süre riski", "Zamanaşımı, hak düşürücü süre veya usulî başvuru süresi itirazı yapılabilir.", "Başlangıç ve kesilme olayları", "Tarihleri belgeleyip alternatif hesap yapmak"),
        ("Görev/yetki ve ön şart", "Yanlış merci, yer veya tamamlanmamış dava şartı itirazı yapılabilir.", "Usulî ret veya bekletici sorun", "Forum adayları ve zorunlu başvuru kanıtı"),
        ("Karşı talep ve denkleştirme", "Karşı taraf takas, mahsup, kusur, ifa veya karşı zarar iddiası kurabilir.", "Net talep hesabı", "Karşı hesap ve sözleşme istisnaları"),
    ]
    return [
        CounterArgument(title, f"{role_mapping.opposing_role} bakımından test edilmesi gereken karşı tez: {argument} Pozisyon: {position}", burden, focus, 0.35)
        for title, argument, burden, focus in stems
    ]


def _rebutting_evidence(counter_args: list[CounterArgument], documents: list[Any]) -> list[EvidenceBlock]:
    evidence: list[EvidenceBlock] = []
    for document in documents:
        body = str(getattr(document, "body", "")).strip()
        if body:
            evidence.append(
                EvidenceBlock(
                    claim="Belge, karşı argümanın çürütülmesi için incelenebilir.",
                    source_type=str(getattr(document, "source", "document")),
                    citation_key=str(getattr(document, "id", "")),
                    full_citation=str(getattr(document, "citation", "")),
                    short_quote=body[:240],
                    document_id=str(getattr(document, "id", "")),
                    temporal_status="document-date-not-resolved",
                    relevance="medium",
                    confidence=0.35,
                )
            )
    return evidence[:3]


def _weak_points(result_data: dict[str, Any]) -> list[WeakPoint]:
    points: list[WeakPoint] = []
    if result_data["missing_facts"]:
        points.append(WeakPoint("Eksik kronoloji/vakıa", "Olay veya dava tarihleri/başlangıç olayları tam değil.", "Süre, yürürlük ve strateji sıralaması değişebilir.", 0.9))
    if not result_data["rebutting_evidence"]:
        points.append(WeakPoint("Kaynak açığı", "Karşı argümanları doğrudan destekleyen belge bulunmadı.", "Çürütme bölümü varsayımsal kalır.", 0.85))
    if not result_data["forum_candidates"]:
        points.append(WeakPoint("Forum belirsizliği", "Görev ve yetki için yeterli olay sinyali yok.", "Yanlış merci ve süre riski doğabilir.", 0.8))
    return points


def _assistant_instructions(
    jurisdiction_ids: list[str] | None = None,
    expert_lenses: list[str] | None = None,
    quality_profile: str = "auto",
    model_hint: str = "",
    question: str = "",
    documents: list[Any] | None = None,
) -> str:
    base = (
        "Bu sonuç nihai hukuki görüş değildir; nonbinding=true, yalnızca bağlayıcı olmayan araştırma/analiz taslağıdır. "
        "Her iddiayı ilgili kaynak türü, künye, belge kimliği ve kısa alıntıyla göster; tarih ve yürürlük "
        "varsayımlarını ayır; çelişen kaynakları koru; kesin süre, kesin görev/yetki veya garanti dili kullanma."
    )
    ids = jurisdiction_ids or []
    persona = compose_persona_instructions(ids, expert_lenses or [])
    reasoning = build_reasoning_instructions(
        ids,
        source_context="legal_analysis",
        quality_profile=quality_profile,
        model_hint=model_hint,
        question=question,
        documents=documents or (),
    )
    return "\n\n".join(item for item in (base, persona, reasoning) if item)


async def run_opposing(
    question: str,
    position: str,
    role: str = "davacı",
    jurisdiction_hint: str | None = None,
    source_scope: SourceScope = "targeted",
    selected_source_ids: list[str] | None = None,
    documents: list[Any] | None = None,
    synthesize: bool = False,
    llm_client: LLMClient | None = None,
    document_backend: Any | None = None,
    temporal_backend: Any | None = None,
    quality_profile: str = "auto",
    model_hint: str = "",
) -> OpposingResult:
    validate_source_scope(source_scope)
    if not settings.enable_aggressive_opposing:
        return OpposingResult(question, "disabled", role, position, source_scope=source_scope)

    mapping = _role_mapping(position, role)
    source_backend = document_backend or IntegratedLegalSourceBackend()
    retrieval_errors: list[str] = []
    documents_were_provided = documents is not None
    if documents is None:
        try:
            if hasattr(source_backend, "search_documents"):
                documents = await source_backend.search_documents(question, 50)
            else:
                documents = await source_backend.search(question, 50)
        except Exception as exc:
            documents = []
            retrieval_errors.append(f"decision retrieval failed: {type(exc).__name__}")
    documents = list(documents or [])
    resolved_temporal_backend = temporal_backend
    if resolved_temporal_backend is None and all(
        hasattr(source_backend, name)
        for name in ("search_norms", "search_invalidation_events", "search_procedural_rules")
    ):
        resolved_temporal_backend = source_backend
    temporal = await TemporalLegalContextBuilder().build(
        question,
        jurisdiction_hint,
        source_scope,
        selected_source_ids,
        backend=resolved_temporal_backend,
    )
    selection = guess_jurisdictions(question)
    jurisdiction_ids = list(dict.fromkeys(
        ([jurisdiction_hint] if jurisdiction_hint else [])
        + [selection.primary, *selection.supporting]
    ))
    if not jurisdiction_ids:
        jurisdiction_ids = ["hukuk"]
    operational_context = OperationalContextBuilder().build(question, jurisdiction_ids, documents=documents)
    try:
        profile = load_profile(jurisdiction_hint or "hukuk")
    except JurisdictionNotFoundError:
        profile = JurisdictionProfile(id=jurisdiction_hint or "hukuk", name=jurisdiction_hint or "Hukuk")
    deadlines = LimitationAndPreclusionAnalyzer().analyze(question, temporal, profile)
    forums = ForumAndDeadlineAnalyzer().analyze(
        question, temporal, profile, documents, source_scope, selected_source_ids
    )
    strategies = StrategicPathPlanner().plan(
        question, position, temporal, forums, documents, source_scope, selected_source_ids
    )
    counters = _counter_arguments(position, mapping)
    rebutting_search = RebuttingCaseSearch(source_backend)
    if documents_were_provided and document_backend is None:
        rebutting = _rebutting_evidence(counters, documents)
    else:
        rebutting = await rebutting_search.search(
            counters, source_scope, selected_source_ids, limit=3
        )
    evidence = _rebutting_evidence(counters, documents) + list(rebutting)
    missing_facts = list(dict.fromkeys([*temporal.missing_facts, *operational_context.unknowns]))
    assumptions = list(temporal.assumptions)
    assumptions.extend(retrieval_errors)
    assumptions.extend(rebutting_search.errors)
    result = OpposingResult(
        question=question,
        mode="server-synthesized" if synthesize and llm_client else "host-orchestrated",
        role=role,
        position=position,
        counter_arguments=counters,
        rebutting_evidence=rebutting,
        temporal_context=temporal,
        deadline_risks=deadlines,
        forum_candidates=forums,
        strategy_options=strategies,
        evidence=evidence,
        assistant_instructions=_assistant_instructions(
            jurisdiction_ids=jurisdiction_ids,
            expert_lenses=selection.expert_lenses,
            quality_profile=quality_profile,
            model_hint=model_hint,
            question=question,
            documents=documents,
        ),
        confidence=min(temporal.confidence, 0.7),
        assumptions=assumptions,
        missing_facts=missing_facts,
        source_scope=source_scope,
        operational_context=operational_context.to_dict(),
    )
    result.weak_points = _weak_points(result.to_dict())
    if synthesize and llm_client:
        result.answer = await llm_client.generate(result.assistant_instructions or "", str(result.to_dict()))
    return result
