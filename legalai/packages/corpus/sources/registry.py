from __future__ import annotations

from dataclasses import KW_ONLY, dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Literal

import yaml

from legalai.packages.corpus.federated import SourceSearchResult


SearchFn = Callable[[str, int], Awaitable[list[SourceSearchResult]]]
SourceStatus = Literal["live_ready", "corpus_only", "verification_pending", "disabled"]


@dataclass(frozen=True)
class SourceDescriptor:
    source_id: str
    label: str
    category: str
    priority: int
    live_supported: bool = True
    local_supported: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    _: KW_ONLY
    status: SourceStatus = "live_ready"
    authority_level: str = "unknown"
    source_kind: str = "official"
    allowed_contexts: tuple[str, ...] = ()


class FunctionSourceAdapter:
    def __init__(self, descriptor: SourceDescriptor, search_fn: SearchFn) -> None:
        self.descriptor = descriptor
        self.source_id = descriptor.source_id
        self._search_fn = search_fn

    async def search(self, query: str, limit: int) -> list[SourceSearchResult]:
        return await self._search_fn(query, limit)


class SourceRegistry:
    def __init__(self, descriptors: list[SourceDescriptor] | None = None) -> None:
        self._descriptors = {item.source_id: item for item in descriptors or []}

    def register(self, descriptor: SourceDescriptor) -> None:
        self._descriptors[descriptor.source_id] = descriptor

    def get(self, source_id: str) -> SourceDescriptor | None:
        return self._descriptors.get(source_id)

    def all(self) -> tuple[SourceDescriptor, ...]:
        return tuple(sorted(self._descriptors.values(), key=lambda item: (item.priority, item.source_id)))


def default_source_registry() -> SourceRegistry:
    return SourceRegistry([
        SourceDescriptor("reklam_kurulu", "Reklam Kurulu kararları", "official_institution", 45, metadata={"institution": "Ticaret Bakanlığı Reklam Kurulu"}, authority_level="domestic_institution_decision", source_kind="institution_decision", allowed_contexts=("legal_analysis", "consumer_research")),
        SourceDescriptor("rekabet_kurumu", "Rekabet Kurumu kararları, mevzuat, kılavuz ve sektör raporları", "official_regulator", 10, authority_level="domestic_institution_decision", source_kind="institution_decision", allowed_contexts=("competition_research", "legal_analysis")),
        SourceDescriptor("rekabet_kurumu_mevzuat", "Rekabet Kurumu mevzuatı", "official_regulator", 10, status="corpus_only", authority_level="domestic_official_guidance", source_kind="official_guidance", allowed_contexts=("legal_analysis", "competition_research", "regulatory_analysis")),
        SourceDescriptor("rekabet_authority_sector_reports", "Rekabet Kurumu sektör raporları", "reports", 15, status="corpus_only", authority_level="domestic_official_research", source_kind="official_research_report", allowed_contexts=("legal_analysis", "competition_research", "doctrine_research")),
        SourceDescriptor("oecd_competition", "OECD rekabet kaynakları", "international_policy", 10, authority_level="non_binding_policy_reference", source_kind="policy_reference", allowed_contexts=("competition_research", "economic_analysis")),
        SourceDescriptor("eu_commission_competition", "AB Komisyonu rekabet kaynakları", "international_official", 10, authority_level="comparative_institution_reference", source_kind="foreign_institution_decision", allowed_contexts=("competition_research", "legal_analysis")),
        SourceDescriptor("eu_court_competition", "ABAD rekabet kararları", "international_court", 10, authority_level="comparative_judicial_reference", source_kind="foreign_judicial_decision", allowed_contexts=("competition_research", "legal_analysis")),
        SourceDescriptor("dg_comp", "Avrupa Komisyonu DG COMP kaynakları", "international_official", 15, authority_level="comparative_institution_reference", source_kind="foreign_institution_decision", allowed_contexts=("competition_research", "legal_analysis")),
        SourceDescriptor("curia", "CURIA / ABAD ve Genel Mahkeme kararları", "international_court", 15, authority_level="comparative_judicial_reference", source_kind="foreign_judicial_decision", allowed_contexts=("competition_research", "legal_analysis")),
        SourceDescriptor("eur_lex_competition", "EUR-Lex rekabet mevzuatı ve resmi yayınları", "international_legislation", 15, status="corpus_only", authority_level="comparative_legislation", source_kind="foreign_legislation", allowed_contexts=("competition_research", "legal_analysis")),
        SourceDescriptor("kvkk", "KVKK Kurul/ilke kararları ve rehberler", "official_regulator", 20, authority_level="domestic_institution_decision", source_kind="institution_decision", allowed_contexts=("legal_analysis", "regulatory_analysis", "kvkk_research")),
        SourceDescriptor("kik", "Kamu İhale Kurulu kararları", "official_regulator", 30, authority_level="domestic_institution_decision", source_kind="institution_decision", allowed_contexts=("legal_analysis", "public_procurement_research")),
        SourceDescriptor("tihek", "TİHEK kararları", "official_institution", 40, authority_level="domestic_institution_decision", source_kind="institution_decision", allowed_contexts=("legal_analysis", "human_rights_research")),
        SourceDescriptor("kdk", "Kamu Denetçiliği Kurumu kararları", "official_institution", 50, authority_level="domestic_institution_decision", source_kind="institution_decision", allowed_contexts=("legal_analysis", "administrative_research")),
        SourceDescriptor("bam", "Bölge Adliye Mahkemeleri", "official_court", 55, authority_level="domestic_judicial_reference", source_kind="judicial_decision", allowed_contexts=("legal_analysis", "civil_research")),
        SourceDescriptor("bim", "Bölge İdare Mahkemeleri", "official_court", 55, live_supported=False, status="verification_pending", authority_level="domestic_judicial_reference", source_kind="judicial_decision", allowed_contexts=("legal_analysis", "administrative_research")),
        SourceDescriptor("idare_mahkemeleri", "Birinci derece idare mahkemeleri", "official_court", 55, authority_level="domestic_judicial_reference", source_kind="judicial_decision", allowed_contexts=("legal_analysis", "administrative_research")),
        SourceDescriptor("bddk", "BDDK kararları ve düzenlemeleri", "official_regulator", 60, authority_level="domestic_institution_decision", source_kind="institution_decision", allowed_contexts=("legal_analysis", "regulatory_analysis")),
        SourceDescriptor("spk", "SPK kararları ve mevzuatı", "official_regulator", 60, authority_level="domestic_institution_decision", source_kind="institution_decision", allowed_contexts=("legal_analysis", "regulatory_analysis")),
        SourceDescriptor("rtuk", "RTÜK kararları", "official_regulator", 60, authority_level="domestic_institution_decision", source_kind="institution_decision", allowed_contexts=("legal_analysis", "regulatory_analysis")),
        SourceDescriptor("epdk", "EPDK kararları", "official_regulator", 60, authority_level="domestic_institution_decision", source_kind="institution_decision", allowed_contexts=("legal_analysis", "regulatory_analysis")),
        SourceDescriptor("btk", "BTK kararları", "official_regulator", 60, authority_level="domestic_institution_decision", source_kind="institution_decision", allowed_contexts=("legal_analysis", "regulatory_analysis")),
        SourceDescriptor("kgk", "KGK kararları ve standartları", "official_institution", 60, authority_level="domestic_institution_decision", source_kind="institution_decision", allowed_contexts=("legal_analysis", "regulatory_analysis")),
        SourceDescriptor("gib", "GİB özelge ve kaynakları", "official_institution", 60, authority_level="domestic_institution_decision", source_kind="institution_guidance", allowed_contexts=("legal_analysis", "tax_research")),
        SourceDescriptor("sayistay", "Sayıştay kararları", "official_court", 60, authority_level="domestic_judicial_reference", source_kind="judicial_decision", allowed_contexts=("legal_analysis", "administrative_research")),
        SourceDescriptor("sigorta_tahkim", "Sigorta Tahkim Komisyonu kararları", "official_arbitration", 60, authority_level="domestic_arbitration_reference", source_kind="arbitration_decision", allowed_contexts=("legal_analysis", "insurance_research")),
        SourceDescriptor("uyusmazlik", "Uyuşmazlık Mahkemesi kararları", "official_court", 60, authority_level="domestic_judicial_reference", source_kind="judicial_decision", allowed_contexts=("legal_analysis",)),
        SourceDescriptor("emsal", "Emsal kararlar", "official_court", 60, authority_level="domestic_judicial_reference", source_kind="judicial_decision", allowed_contexts=("legal_analysis",)),
        SourceDescriptor("yargitay", "Yargıtay kararları", "official_court", 60, authority_level="domestic_high_court_reference", source_kind="judicial_decision", allowed_contexts=("legal_analysis",)),
        SourceDescriptor("danistay", "Danıştay kararları", "official_court", 60, authority_level="domestic_high_court_reference", source_kind="judicial_decision", allowed_contexts=("legal_analysis", "administrative_research")),
        SourceDescriptor("aym", "Anayasa Mahkemesi kararları", "constitutional_court", 60, authority_level="constitutional_court_reference", source_kind="judicial_decision", allowed_contexts=("legal_analysis", "constitutional_research")),
        SourceDescriptor("aihm_hudoc", "AİHM/HUDOC kararları", "international_court", 60, authority_level="comparative_judicial_reference", source_kind="foreign_judicial_decision", allowed_contexts=("legal_analysis", "human_rights_research")),
        SourceDescriptor("bedesten", "Bedesten canlı karar araması", "upstream_live", 60, local_supported=False, authority_level="domestic_judicial_reference", source_kind="judicial_decision", allowed_contexts=("legal_analysis",)),
        SourceDescriptor("dergipark_and_open_doctrine", "DergiPark ve açık doktrin", "academic", 70, status="corpus_only", authority_level="non_binding_doctrine", source_kind="academic_reference", allowed_contexts=("legal_analysis", "doctrine_research")),
        SourceDescriptor("baro_and_tbb_journals", "Baro ve TBB dergileri", "academic", 70, status="corpus_only", authority_level="non_binding_doctrine", source_kind="academic_reference", allowed_contexts=("legal_analysis", "doctrine_research")),
        SourceDescriptor("yok_public_law_theses", "YÖK kamuya açık hukuk tezleri", "academic", 70, status="corpus_only", authority_level="non_binding_doctrine", source_kind="academic_reference", allowed_contexts=("legal_analysis", "doctrine_research")),
        SourceDescriptor("rekabet_authority_expert_theses", "Rekabet Kurumu uzmanlık tezleri", "academic", 70, status="corpus_only", authority_level="non_binding_doctrine", source_kind="academic_reference", allowed_contexts=("legal_analysis", "competition_research", "doctrine_research")),
        SourceDescriptor("rekabet_journal", "Rekabet Dergisi", "academic", 70, status="corpus_only", authority_level="non_binding_doctrine", source_kind="academic_reference", allowed_contexts=("legal_analysis", "competition_research", "doctrine_research")),
        SourceDescriptor("competition_reports", "Rekabet ve piyasa raporları", "reports", 75, status="corpus_only", authority_level="non_binding_economic_reference", source_kind="economic_report", allowed_contexts=("competition_research", "economic_analysis"), metadata={"precedential": False, "role": "economic_factual_support"}),
        SourceDescriptor("institution_reports", "Kamu kurumlarının faaliyet ve sektör raporları", "reports", 75, status="corpus_only", authority_level="non_binding_economic_reference", source_kind="institution_report", allowed_contexts=("legal_analysis", "economic_analysis", "regulatory_analysis"), metadata={"precedential": False, "role": "economic_factual_support"}),
        SourceDescriptor("ticaret_bakanligi_ithalat", "Ticaret Bakanlığı İthalat kaynakları", "official_regulator", 25, status="corpus_only", authority_level="domestic_institution_decision", source_kind="institution_decision", allowed_contexts=("legal_analysis", "trade_defense_research")),
        SourceDescriptor("wto_trade_remedy_agreements", "DTÖ ticaret savunması anlaşmaları", "international_legislation", 25, status="corpus_only", authority_level="comparative_legislation", source_kind="foreign_legislation", allowed_contexts=("trade_defense_research", "legal_analysis")),
        SourceDescriptor("eu_trade_defense_regulations", "AB ticaret savunması mevzuatı", "international_official", 25, status="corpus_only", authority_level="comparative_institution_reference", source_kind="foreign_institution_decision", allowed_contexts=("trade_defense_research", "legal_analysis")),
        SourceDescriptor("eu_court_trade_defense", "ABAD ticaret savunması kararları", "international_court", 25, status="corpus_only", authority_level="comparative_judicial_reference", source_kind="foreign_judicial_decision", allowed_contexts=("trade_defense_research", "legal_analysis")),
        SourceDescriptor("us_trade_remedy_determinations", "ABD ticaret savunması tespitleri", "international_official", 25, status="corpus_only", authority_level="comparative_institution_reference", source_kind="foreign_institution_decision", allowed_contexts=("trade_defense_research", "legal_analysis")),
        SourceDescriptor("trade_defense_doctrine", "Ticaret savunması doktrini", "academic", 70, status="corpus_only", authority_level="non_binding_doctrine", source_kind="doctrine", allowed_contexts=("trade_defense_research", "doctrine_research")),
    ])


def load_source_metadata(config_dir: Path) -> list[dict[str, Any]]:
    """Load source metadata files used by the registry validation boundary."""
    entries: list[dict[str, Any]] = []
    for path in sorted(config_dir.glob("*.yaml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for entry in payload.get("sources", []):
            if not isinstance(entry, dict) or not entry.get("source_id"):
                raise ValueError(f"Geçersiz kaynak metadata kaydı: {path.name}")
            entries.append(dict(entry))
    return entries


def validate_source_metadata(
    registry: SourceRegistry,
    entries: list[dict[str, Any]],
) -> None:
    """Reject status, authority or context drift between YAML and registry."""
    for entry in entries:
        source_id = str(entry["source_id"])
        descriptor = registry.get(source_id)
        if descriptor is None:
            raise ValueError(f"Registry'de bulunmayan kaynak metadata'sı: {source_id}")
        checks = {
            "status": (entry.get("status", descriptor.status), descriptor.status),
            "authority_level": (entry.get("authority_level"), descriptor.authority_level),
        }
        for field_name, (actual, expected) in checks.items():
            if actual != expected:
                raise ValueError(
                    f"Kaynak metadata uyumsuzluğu: {source_id}.{field_name} "
                    f"{actual!r} != {expected!r}"
                )
        actual_contexts = set(entry.get("allowed_contexts", ()))
        expected_contexts = set(descriptor.allowed_contexts)
        if actual_contexts != expected_contexts:
            raise ValueError(
                f"Kaynak metadata uyumsuzluğu: {source_id}.allowed_contexts "
                f"{actual_contexts!r} != {expected_contexts!r}"
            )
