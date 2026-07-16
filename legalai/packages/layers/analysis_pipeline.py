"""run_pipeline — `katmanli_analiz` MCP aracı ve `POST /api/v1/analyze`
HTTP endpoint'inin ortak çağırdığı tek iş mantığı. Bkz.
FORK-KAPSAMLI-PLAN.md §2.6 ve §5.3, Hafta 7.

`synthesize` parametresi — MCP mimarisinin temel bir gerçeğini yansıtır:
MCP sunucusu bir LLM DEĞİLDİR, sadece araç sağlar; cevabı normalde bu
aracı ÇAĞIRAN host model (Cursor/Claude Desktop/ChatGPT-Codex/Antigravity
içindeki, kullanıcının ZATEN sahip olduğu abonelikle çalışan model)
üretir. Bu yüzden:

- `synthesize=False` (MCP tool varsayılanı): `GroundedGenerator` ve
  `VerifiedCitationCheck` katmanları ATLANIR — hiçbir API anahtarı
  gerekmez. Pipeline sadece gerçek belgeleri + ratio/dictum/karşı-oy/
  argüman-gücü analizini döndürür; nihai, kaynaklı cevabı YAZMA işini
  `assistant_instructions` talimatıyla birlikte host modele bırakır.
- `synthesize=True` (HTTP endpoint varsayılanı): host model devrede
  olmadığı senaryolar için (örn. gelecekteki web UI/otomasyon)
  `LLMRouter` üzerinden gerçek bir LLM çağrısı yapılır — bunun için
  `.env`'de bir API anahtarı GEREKİR.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from legalai.packages.layers.argument_strength_scorer import ArgumentStrengthScorer
from legalai.packages.layers.citation_transfer_filter import CitationTransferFilter
from legalai.packages.layers.dissent_detector import DissentDetector
from legalai.packages.layers.grounded_generator import GroundedGenerator
from legalai.packages.layers.pipeline import Context, Layer, Pipeline
from legalai.packages.layers.qualify_issue import QualifyIssue
from legalai.packages.layers.ratio_dictum import RatioDictumFilter
from legalai.packages.layers.rerank import Rerank
from legalai.packages.layers.retrieve_documents import RetrieveDocuments
from legalai.packages.layers.select_jurisdiction_profile import SelectJurisdictionProfile
from legalai.packages.layers.verified_citation_check import VerifiedCitationCheck
from legalai.packages.layers.temporal_context import TemporalLegalContextBuilder
from legalai.packages.shared.tenant import current_tenant
from legalai.packages.shared.types import Document


@dataclass
class AnalysisResult:
    """`Context`'in dışa açılan (MCP/HTTP) sonuç görünümü."""

    question: str
    mode: str
    jurisdiction_id: str | None
    answer: str | None
    citations: list[str]
    ratios: list[Any]
    dictums: list[Any]
    dissents: list[Any]
    argument_scores: list[Any]
    documents: list[Document]
    trace: list[dict[str, Any]]
    assistant_instructions: str | None = None
    temporal_context: Any | None = None
    evidence: list[Any] = field(default_factory=list)
    deadline_risks: list[Any] = field(default_factory=list)
    forum_candidates: list[Any] = field(default_factory=list)
    strategy_options: list[Any] = field(default_factory=list)
    analysis_only: bool = True
    non_binding: bool = True
    confidence: float = 0.0
    assumptions: list[str] = field(default_factory=list)
    missing_facts: list[str] = field(default_factory=list)
    source_scope: str = "targeted"

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "question": self.question,
            "mode": self.mode,
            "jurisdiction_id": self.jurisdiction_id,
            "answer": self.answer,
            "citations": self.citations,
            "sources": [
                {"doc_id": doc.id, "citation": doc.citation, "source": doc.source}
                for doc in self.documents
            ],
            "ratios": self.ratios,
            "dictums": self.dictums,
            "dissents": self.dissents,
            "argument_scores": self.argument_scores,
            "trace": self.trace,
            "temporal_context": _jsonish(self.temporal_context),
            "evidence": [_jsonish(item) for item in (self.evidence or [])],
            "deadline_risks": [_jsonish(item) for item in (self.deadline_risks or [])],
            "forum_candidates": [_jsonish(item) for item in (self.forum_candidates or [])],
            "strategy_options": [_jsonish(item) for item in (self.strategy_options or [])],
            "analysis_only": True,
            "non_binding": True,
            "confidence": self.confidence,
            "assumptions": list(self.assumptions or []),
            "missing_facts": list(self.missing_facts or []),
            "source_scope": self.source_scope,
        }
        if self.assistant_instructions is not None:
            payload["assistant_instructions"] = self.assistant_instructions
        return payload


def _jsonish(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if hasattr(value, "__dict__"):
        return {key: _jsonish(item) for key, item in value.__dict__.items()}
    if isinstance(value, list):
        return [_jsonish(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonish(item) for key, item in value.items()}
    return value


def build_assistant_instructions(valid_doc_ids: list[str]) -> str:
    """`synthesize=False` modunda, host modele (bu aracı çağıran Cursor/
    Claude/ChatGPT/Antigravity vb. asistana) nihai cevabı NASIL yazması
    gerektiğini anlatan talimat. Bkz. modül docstring'i."""
    ids_repr = ", ".join(f"#{doc_id}" for doc_id in valid_doc_ids) or "(hiçbir belge bulunamadı)"
    return (
        "Bu araç bir LLM DEĞİLDİR; sadece belge + analiz getirir. Kullanıcının "
        "sorusunu SEN (bu aracı çağıran asistan) cevapla. Kurallar: "
        "(1) SADECE 'documents', 'ratios', 'dictums', 'dissents', "
        "'argument_scores' alanlarındaki bilgiyi kullan, başka bilgi uydurma. "
        "(2) Cevabındaki HER iddiayı [#belge_id] biçiminde kaynak göster; "
        f"SADECE şu id'leri kullan: {ids_repr}. "
        "(3) Belgelerde soruya cevap yoksa bunu açıkça söyle. "
        "(4) 'dissents' varsa kararın tartışmalı olabileceğini belirt. "
        "(5) Bu bir taslak/araştırma yardımıdır, hukuki tavsiye değildir — "
        "cevabının sonuna bunu ekle."
    )


def build_layered_pipeline(
    retrieve: Layer | None = None,
    generator: GroundedGenerator | None = None,
    rerank_top_k: int = 5,
    synthesize: bool = True,
) -> Pipeline:
    """§5.3 diyagramına (QualifyIssue → ... → GroundedGenerator) Hafta 7
    agent promptundaki "retrieve + rerank" talimatı eklenmiş tam pipeline.

    `synthesize=True` ise `GroundedGenerator`+`VerifiedCitationCheck` de
    pipeline'a eklenir (LLM API anahtarı gerektirir — bkz. modül
    docstring'i). `synthesize=False` ise bu iki katman ATLANIR; nihai
    cevabı host model üretir."""
    layers: list[Layer] = [
        QualifyIssue(),
        SelectJurisdictionProfile(),
        retrieve or RetrieveDocuments(),
        RatioDictumFilter(),
        DissentDetector(),
        CitationTransferFilter(),
        ArgumentStrengthScorer(),
        Rerank(top_k=rerank_top_k),
    ]
    if synthesize:
        shared_generator = generator or GroundedGenerator()
        layers.extend([shared_generator, VerifiedCitationCheck(generator=shared_generator)])
    return Pipeline(layers=layers)


async def run_pipeline(
    question: str,
    mode: str = "layered",
    jurisdiction_hint: str | None = None,
    documents: list[Document] | None = None,
    pipeline: Pipeline | None = None,
    synthesize: bool = True,
) -> AnalysisResult:
    """Bkz. §2.6 — MCP tool ve HTTP endpoint bu fonksiyonu çağırır.

    `documents` verilirse (örn. test fixture'ı veya `decision_id` akışı)
    `RetrieveDocuments` katmanı gerçek arama yapmaz, verilenleri kullanır.

    `synthesize=False` (MCP tool varsayılanı) API anahtarı GEREKTİRMEZ —
    bkz. modül docstring'i. `pipeline` açıkça verilirse `synthesize`
    parametresi yok sayılır (çağıran taraf pipeline'ı kendi kurmuştur).
    """
    tenant = current_tenant()
    ctx = Context(
        tenant_id=tenant.tenant_id,
        question=question,
        mode=mode,
        jurisdiction_id=jurisdiction_hint,
        documents=list(documents) if documents else [],
    )

    active_pipeline = pipeline or build_layered_pipeline(synthesize=synthesize)
    result_ctx = await active_pipeline.run(ctx)

    assistant_instructions = None
    if not synthesize and pipeline is None:
        assistant_instructions = build_assistant_instructions([doc.id for doc in result_ctx.documents])
        assistant_instructions += (
            " Ayrıca evidence alanındaki kaynak türü, tam künye ve kısa ilgili alıntıyı "
            "ilgili iddianın yanında göster; temporal_context, deadline_risks, "
            "forum_candidates ve strategy_options belirsizliklerini açıkla. "
            "Bu çıktı nonbinding, analysis-only araştırma taslağıdır; kesin görüş veya garanti değildir."
        )

    return AnalysisResult(
        question=result_ctx.question,
        mode=result_ctx.mode,
        jurisdiction_id=result_ctx.jurisdiction_id,
        answer=result_ctx.answer,
        citations=result_ctx.citations,
        ratios=result_ctx.ratios,
        dictums=result_ctx.dictums,
        dissents=result_ctx.dissents,
        argument_scores=result_ctx.argument_scores,
        documents=result_ctx.documents,
        trace=result_ctx.trace,
        assistant_instructions=assistant_instructions,
        temporal_context=await TemporalLegalContextBuilder().build(question),
        evidence=list(result_ctx.evidence),
        deadline_risks=[],
        forum_candidates=list(result_ctx.forum_candidates),
        strategy_options=list(result_ctx.strategy_options),
        assumptions=[],
        missing_facts=[],
    )
