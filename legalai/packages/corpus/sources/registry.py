from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from legalai.packages.corpus.federated import SourceSearchResult


SearchFn = Callable[[str, int], Awaitable[list[SourceSearchResult]]]


@dataclass(frozen=True)
class SourceDescriptor:
    source_id: str
    label: str
    category: str
    priority: int
    live_supported: bool = True
    local_supported: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


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
        SourceDescriptor("reklam_kurulu", "Reklam Kurulu kararları", "official_institution", 45, metadata={"institution": "Ticaret Bakanlığı Reklam Kurulu"}),
        SourceDescriptor("rekabet_kurumu", "Rekabet Kurumu kararları, mevzuat, kılavuz ve sektör raporları", "official_regulator", 10),
        SourceDescriptor("oecd_competition", "OECD rekabet kaynakları", "international_policy", 10),
        SourceDescriptor("eu_commission_competition", "AB Komisyonu rekabet kaynakları", "international_official", 10),
        SourceDescriptor("eu_court_competition", "ABAD rekabet kararları", "international_court", 10),
        SourceDescriptor("kvkk", "KVKK Kurul/ilke kararları ve rehberler", "official_regulator", 20),
        SourceDescriptor("kik", "Kamu İhale Kurulu kararları", "official_regulator", 30),
        SourceDescriptor("tihek", "TİHEK kararları", "official_institution", 40),
        SourceDescriptor("kdk", "Kamu Denetçiliği Kurumu kararları", "official_institution", 50),
        SourceDescriptor("bddk", "BDDK kararları ve düzenlemeleri", "official_regulator", 60),
        SourceDescriptor("spk", "SPK kararları ve mevzuatı", "official_regulator", 60),
        SourceDescriptor("rtuk", "RTÜK kararları", "official_regulator", 60),
        SourceDescriptor("epdk", "EPDK kararları", "official_regulator", 60),
        SourceDescriptor("btk", "BTK kararları", "official_regulator", 60),
        SourceDescriptor("kgk", "KGK kararları ve standartları", "official_institution", 60),
        SourceDescriptor("gib", "GİB özelge ve kaynakları", "official_institution", 60),
        SourceDescriptor("sayistay", "Sayıştay kararları", "official_court", 60),
        SourceDescriptor("sigorta_tahkim", "Sigorta Tahkim Komisyonu kararları", "official_arbitration", 60),
        SourceDescriptor("uyusmazlik", "Uyuşmazlık Mahkemesi kararları", "official_court", 60),
        SourceDescriptor("emsal", "Emsal kararlar", "official_court", 60),
        SourceDescriptor("yargitay", "Yargıtay kararları", "official_court", 60),
        SourceDescriptor("danistay", "Danıştay kararları", "official_court", 60),
        SourceDescriptor("aym", "Anayasa Mahkemesi kararları", "constitutional_court", 60),
        SourceDescriptor("aihm_hudoc", "AİHM/HUDOC kararları", "international_court", 60),
        SourceDescriptor("bedesten", "Bedesten canlı karar araması", "upstream_live", 60, local_supported=False),
        SourceDescriptor("dergipark_and_open_doctrine", "DergiPark ve açık doktrin", "academic", 70),
        SourceDescriptor("baro_and_tbb_journals", "Baro ve TBB dergileri", "academic", 70),
        SourceDescriptor("yok_public_law_theses", "YÖK kamuya açık hukuk tezleri", "academic", 70),
        SourceDescriptor("rekabet_authority_expert_theses", "Rekabet Kurumu uzmanlık tezleri", "academic", 70),
        SourceDescriptor("rekabet_journal", "Rekabet Dergisi", "academic", 70),
    ])
