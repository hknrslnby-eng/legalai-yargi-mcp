"""Baglama gore resmi kaynaklar icin capraz sorgu plani uretir.

Kaynak secimi salt soru metnindeki anahtar kelimelere birakilmaz. Jurisdiction
ve uzmanlik lensleri, ilgili resmi kaynaklari planlamak icin birincil sinyaldir;
keyword gating yalnizca eski adapter API'si icin geriye donuk bir guvenlik
mekanizmasi olarak kalir.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from collections.abc import Sequence

from legalai.packages.corpus.sources.registry import SourceRegistry, default_source_registry


@dataclass(frozen=True)
class SourceSubQuery:
    source_id: str
    query: str
    rationale: str
    status: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class SourceQueryPlan:
    subqueries: tuple[SourceSubQuery, ...]
    skipped: tuple[SourceSubQuery, ...] = ()

    def to_dict(self) -> dict[str, list[dict[str, str]]]:
        return {
            "subqueries": [item.to_dict() for item in self.subqueries],
            "skipped": [item.to_dict() for item in self.skipped],
        }


_CONTEXT_SOURCES: dict[str, tuple[str, ...]] = {
    "rekabet": (
        "rekabet_kurumu", "bedesten", "bam", "bim", "danistay", "idare_mahkemeleri",
        "oecd_competition", "dg_comp", "curia", "competition_reports",
    ),
    "ticaret_savunmasi": (
        "ticaret_bakanligi_ithalat", "bedesten", "bam", "danistay",
        "idare_mahkemeleri", "rekabet_kurumu", "oecd_competition",
        "wto_trade_remedy_agreements", "eu_trade_defense_regulations",
        "eu_court_trade_defense", "us_trade_remedy_determinations",
        "trade_defense_doctrine",
    ),
    "kvkk": ("kvkk", "bedesten", "danistay", "idare_mahkemeleri"),
    "idare": ("bedesten", "bam", "bim", "danistay", "idare_mahkemeleri"),
    "ceza": ("bedesten", "yargitay", "danistay"),
}

_LENS_CONTEXTS: dict[str, tuple[str, ...]] = {
    "ekonomi": ("rekabet",),
    "iktisat": ("rekabet",),
    "rekabet": ("rekabet",),
    "ticaret": ("rekabet", "ticaret_savunmasi"),
    "ticaret_savunmasi": ("ticaret_savunmasi",),
    "kvkk": ("kvkk",),
    "nis": ("kvkk",),
    "nis-1": ("kvkk",),
    "nis-2": ("kvkk",),
    "siber_guvenlik": ("kvkk",),
    "siber": ("kvkk",),
    "idare": ("idare",),
    "ceza": ("ceza",),
}


def _normalize(value: str) -> str:
    return (
        value.casefold()
        .replace("ı", "i")
        .replace("ş", "s")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ö", "o")
        .replace("ç", "c")
    )


def _contexts(jurisdiction_ids: Sequence[str], expert_lenses: Sequence[str]) -> list[str]:
    contexts: list[str] = []
    for value in (*jurisdiction_ids, *expert_lenses):
        normalized = _normalize(value)
        if normalized in _CONTEXT_SOURCES and normalized not in contexts:
            contexts.append(normalized)
        for key, mapped in _LENS_CONTEXTS.items():
            if normalized == _normalize(key):
                contexts.extend(item for item in mapped if item not in contexts)
    return contexts


def build_source_query_plan(
    *,
    question: str,
    jurisdiction_ids: Sequence[str],
    expert_lenses: Sequence[str],
    source_scope: str = "targeted",
    selected_source_ids: Sequence[str] = (),
    registry: SourceRegistry | None = None,
) -> SourceQueryPlan:
    """Create deterministic local-plus-live source subqueries.

    Explicit source selection is authoritative. Otherwise, the jurisdiction
    and expert lenses determine the cross-query scope, with ``all`` exposing
    every source whose registry status is ``live_ready``.
    """
    active_registry = registry or default_source_registry()
    local = SourceSubQuery("local_corpus", question, "Yerel corpus her sorguda taranir.", "corpus_only")
    if selected_source_ids:
        candidates = list(dict.fromkeys(selected_source_ids))
        rationale = "Kullanici tarafindan acikca secilen kaynak."
    elif source_scope == "all":
        candidates = [item.source_id for item in active_registry.all() if item.status == "live_ready"]
        rationale = "Tum live_ready resmi kaynaklar baglama acik capraz sorgu icin planlandi."
    else:
        contexts = _contexts(jurisdiction_ids, expert_lenses)
        candidates = list(dict.fromkeys(
            source_id
            for context in contexts
            for source_id in _CONTEXT_SOURCES.get(context, ())
        ))
        rationale = "Jurisdiction ve uzmanlik lensi ile baglanti algilandigi icin planlandi."

    subqueries = [local]
    skipped: list[SourceSubQuery] = []
    for source_id in candidates:
        descriptor = active_registry.get(source_id)
        if descriptor is None:
            skipped.append(SourceSubQuery(source_id, question, "Kaynak registry'de tanimli degil.", "disabled"))
            continue
        if descriptor.status != "live_ready":
            skipped.append(SourceSubQuery(
                source_id,
                question,
                f"Kaynak durumu {descriptor.status}; canli adapter kullanimi atlandi.",
                descriptor.status,
            ))
            continue
        subqueries.append(SourceSubQuery(source_id, question, rationale, descriptor.status))
    return SourceQueryPlan(tuple(subqueries), tuple(skipped))
