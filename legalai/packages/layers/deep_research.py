"""derin_arastirma — Hafta 8. Bkz. FORK-KAPSAMLI-PLAN.md §5.2.

İKİ ÇALIŞMA MODU (bkz. Hafta 7 pivotundaki `synthesize` mantığı, §2.6):

- **`synthesize=False`** (API anahtarı YOKSA varsayılan/otomatik): sunucu
  kendi Planner/Critic/Editor LLM çağrısı YAPMAZ. Jurisdiction profile'ın
  `axes` alanından türetilmiş ADAY alt sorular + host modele (bu aracı
  çağıran Cursor/Claude Desktop/ChatGPT-Codex/Antigravity asistanı,
  kullanıcının kendi aboneliğiyle çalışır) "her alt soru için
  `katmanli_analiz`'i çağır, sonra `alinti_dogrula` ile kendi taslağını
  kontrol et, sonra sentezle" talimatını döner. Host model = Planner +
  Critic + Editor; sunucu yalnızca Researcher birimini
  (`katmanli_analiz`) ve doğrulama aracını (`alinti_dogrula`) sağlar.
- **`synthesize=True`** (.env'de bir LLM anahtarı VARSA, isteğe bağlı):
  sunucu, §5.2 diyagramındaki Planner→Researcher(N)→Critic→Editor→
  VerifiedCitationCheck döngüsünü TAMAMEN kendi içinde `LLMRouter`
  üzerinden yürütür — kullanıcı isterse kendi API anahtarıyla tam
  otomatik (host modelsiz de çalışabilen) bir sonuç alabilir.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from legalai.packages.jurisdictions.loader import JurisdictionNotFoundError, load_profile
from legalai.packages.layers.analysis_pipeline import run_pipeline
from legalai.packages.layers.qualify_issue import guess_jurisdiction
from legalai.packages.layers.verified_citation_check import extract_citations
from legalai.packages.llm.router import LLMNotConfiguredError, llm_router

_MAX_CRITIC_ROUNDS = 1  # ek ne kadar eleştiri/ek-alt-soru turu yapılabilir (maliyet sınırı)
_MAX_EXTRA_QUESTIONS_PER_ROUND = 2

_PLANNER_SYSTEM_TEMPLATE = (
    "Sen bir Türk hukuku araştırma planlayıcısısın. Kullanıcının sorusunu, "
    "her biri tek bir konuya odaklanan en fazla {depth} alt soruya böl. "
    "SADECE bir JSON dizisi (string listesi) döndür, başka hiçbir metin "
    'ekleme. Örnek: ["alt soru 1", "alt soru 2"]'
)
_CRITIC_SYSTEM = (
    "Sen bir Türk hukuku araştırma eleştirmenisin. Sana orijinal soru ve "
    "şimdiye kadar toplanan alt-cevaplar verilecek. Eksik bir yön varsa "
    "SADECE eksik olan konuları kapsayan YENİ bir JSON dizisi (en fazla 2 "
    "alt soru) döndür. Yeterliyse SADECE boş dizi `[]` döndür. Başka metin "
    "ekleme."
)
_EDITOR_SYSTEM = (
    "Sen bir Türk hukuku editörüsün. Sana orijinal soru ve birden fazla "
    "alt-soru + kaynaklı alt-cevap verilecek. Bunları TEK, tutarlı bir "
    "cevaba sentezle. Alt-cevaplardaki [#belge_id] referanslarını OLDUĞU "
    "GİBİ koru — yeni bir id UYDURMA. Çelişki varsa belirt. Sonuna 'bu bir "
    "taslak/araştırma yardımıdır, hukuki tavsiye değildir' notu ekle."
)


@dataclass
class SubResearch:
    subquestion: str
    answer: str | None
    citations: list[str]
    sources: list[dict[str, str]] = field(default_factory=list)


@dataclass
class DeepResearchResult:
    question: str
    mode: str  # "host_orchestrated" | "server_synthesized"
    subquestions: list[str]
    sub_results: list[SubResearch]
    answer: str | None
    citations: list[str]
    instructions: str | None = None
    evidence: list[dict[str, Any]] = field(default_factory=list)
    temporal_context: dict[str, Any] | None = None
    deadline_risks: list[dict[str, Any]] = field(default_factory=list)
    forum_candidates: list[dict[str, Any]] = field(default_factory=list)
    strategy_options: list[dict[str, Any]] = field(default_factory=list)
    analysis_only: bool = True
    non_binding: bool = True
    confidence: float = 0.0
    assumptions: list[str] = field(default_factory=list)
    missing_facts: list[str] = field(default_factory=list)
    source_scope: str = "targeted"

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "question": self.question,
            "mode": self.mode,
            "subquestions": self.subquestions,
            "sub_results": [
                {
                    "subquestion": r.subquestion,
                    "answer": r.answer,
                    "citations": r.citations,
                    "sources": r.sources,
                }
                for r in self.sub_results
            ],
            "answer": self.answer,
            "citations": self.citations,
            "evidence": self.evidence,
            "temporal_context": self.temporal_context,
            "deadline_risks": self.deadline_risks,
            "forum_candidates": self.forum_candidates,
            "strategy_options": self.strategy_options,
            "analysis_only": True,
            "non_binding": True,
            "confidence": self.confidence,
            "assumptions": self.assumptions,
            "missing_facts": self.missing_facts,
            "source_scope": self.source_scope,
        }
        if self.instructions is not None:
            payload["instructions"] = self.instructions
        return payload


def _llm_available() -> bool:
    try:
        llm_router.route("simple")
        return True
    except LLMNotConfiguredError:
        return False


def suggest_subquestions_from_axes(question: str, jurisdiction_id: str | None, depth: int) -> list[str]:
    """LLM olmadan, jurisdiction profile'ın `axes` alanından deterministik
    ADAY alt sorular üretir. Gerçek bir "planlama" değildir — sadece host
    modele başlangıç noktası verir; host model bunları görmezden gelip
    kendi (daha isabetli) alt sorularını üretebilir."""
    axes: list[str] = []
    if jurisdiction_id:
        try:
            axes = load_profile(jurisdiction_id).axes
        except JurisdictionNotFoundError:
            axes = []
    if not axes:
        return [question]
    readable = [a.replace("_", " ") for a in axes[: max(depth, 1)]]
    return [f"'{question}' sorusunun '{axis}' boyutuyla ilgili durum nedir?" for axis in readable]


def _build_host_orchestrated_instructions(subquestions: list[str]) -> str:
    numbered = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(subquestions))
    return (
        "Bu araç kendi başına derin araştırma YAPMAZ (API anahtarı "
        "yapılandırılmamış); SEN (bu aracı çağıran asistan) Planner + "
        "Researcher + Critic + Editor rolünü üstlen: "
        "(1) Aşağıdaki ADAY alt sorulardan işine yarayanları kullan, "
        "istersen kendi alt sorularını ekle/değiştir (toplam en fazla 5): "
        f"\n{numbered}\n"
        "(2) HER alt soru için `katmanli_analiz` aracını çağır, dönen "
        "`assistant_instructions`'a göre kısa bir alt-cevap yaz. "
        "(3) Tüm alt-cevapları birleştirip TEK bir sentez cevap yaz; "
        "eksik/çelişkili bir şey varsa açıkça belirt. "
        "(4) Sentez cevabını `alinti_dogrula` aracıyla (known_doc_ids = "
        "topladığın tüm belge id'leri) kontrol et; geçersiz [#id] varsa "
        "düzelt. "
        "(5) Cevabın sonuna 'bu bir taslak/araştırma yardımıdır, hukuki "
        "tavsiye değildir' notunu ekle."
    )


async def _run_host_orchestrated(question: str, depth: int) -> DeepResearchResult:
    jurisdiction_id, _ = guess_jurisdiction(question)
    subquestions = suggest_subquestions_from_axes(question, jurisdiction_id, depth)
    return DeepResearchResult(
        question=question,
        mode="host_orchestrated",
        subquestions=subquestions,
        sub_results=[],
        answer=None,
        citations=[],
        instructions=_build_host_orchestrated_instructions(subquestions),
    )


def _parse_json_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    candidate = match.group(0) if match else raw
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item).strip() for item in parsed if str(item).strip()]


async def _research_subquestion(subquestion: str) -> SubResearch:
    result = await run_pipeline(question=subquestion, synthesize=True)
    return SubResearch(
        subquestion=subquestion,
        answer=result.answer,
        citations=result.citations,
        sources=[
            {"doc_id": doc.id, "citation": doc.citation, "source": doc.source}
            for doc in result.documents
        ],
    )


async def _run_server_synthesized(question: str, depth: int) -> DeepResearchResult:
    planner = llm_router.route("reasoning")
    plan_raw = await planner.generate(
        system=_PLANNER_SYSTEM_TEMPLATE.format(depth=depth), user=f"Soru: {question}"
    )
    subquestions = _parse_json_list(plan_raw)[:depth] or [question]

    sub_results = [await _research_subquestion(q) for q in subquestions]

    for _ in range(_MAX_CRITIC_ROUNDS):
        critic = llm_router.route("reasoning")
        summary = "\n".join(
            f"- {r.subquestion}: {(r.answer or '(cevap yok)')[:300]}" for r in sub_results
        )
        critic_raw = await critic.generate(
            system=_CRITIC_SYSTEM, user=f"Orijinal soru: {question}\n\nAlt cevaplar:\n{summary}"
        )
        extra_questions = _parse_json_list(critic_raw)[:_MAX_EXTRA_QUESTIONS_PER_ROUND]
        if not extra_questions:
            break
        for extra_q in extra_questions:
            sub_results.append(await _research_subquestion(extra_q))
            subquestions.append(extra_q)

    editor = llm_router.route("reasoning")
    sub_answers_block = "\n\n".join(
        f"Alt soru: {r.subquestion}\nAlt cevap: {r.answer or '(bulunamadı)'}" for r in sub_results
    )
    final_answer = await editor.generate(
        system=_EDITOR_SYSTEM, user=f"Orijinal soru: {question}\n\n{sub_answers_block}"
    )

    valid_ids = {c for r in sub_results for c in r.citations}
    citations = extract_citations(final_answer)
    invalid = [c for c in citations if c not in valid_ids]
    if invalid:
        fix_hint = (
            f"Şu referanslar geçersiz: {invalid}. SADECE şu id'leri kullan: {sorted(valid_ids)}."
        )
        final_answer = await editor.generate(
            system=_EDITOR_SYSTEM,
            user=f"Orijinal soru: {question}\n\n{sub_answers_block}\n\nDÜZELTME: {fix_hint}",
        )
        citations = [c for c in extract_citations(final_answer) if c in valid_ids]

    return DeepResearchResult(
        question=question,
        mode="server_synthesized",
        subquestions=subquestions,
        sub_results=sub_results,
        answer=final_answer,
        citations=citations,
    )


async def run_deep_research(
    question: str, depth: int = 3, synthesize: bool | None = None
) -> DeepResearchResult:
    """`synthesize=None` (varsayılan) → `.env`'de bir LLM anahtarı VARSA
    otomatik olarak `True`, yoksa `False` davranır (bkz. modül docstring'i)."""
    depth = max(1, min(depth, 5))
    resolved_synthesize = _llm_available() if synthesize is None else synthesize

    if not resolved_synthesize:
        return await _run_host_orchestrated(question, depth)
    return await _run_server_synthesized(question, depth)
