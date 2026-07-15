"""AİHM karar yapısı — normalize edilmiş veri modeli.
Bkz. FORK-KAPSAMLI-PLAN.md §4.4."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class AIHMDecision:
    application_no: str        # "12345/20"
    respondent: str            # "TUR"
    date: date | None
    articles: list[str] = field(default_factory=list)     # ["6", "10", "P1-1"]
    importance: int | None = None                          # 1 (yüksek) — 4
    chamber: str = ""           # "GRANDCHAMBER" | "CHAMBER" | "COMMITTEE" (documentcollectionid'den)
    languages_available: list[str] = field(default_factory=list)
    sections: dict[str, str] = field(default_factory=dict)  # {"procedure": ..., "facts": ..., "law": ..., "operative": ..., "separate": ...}
    votes: dict[str, str] = field(default_factory=dict)     # Hafta 5'te doldurulacak (bkz. §3.2 AIHMProfile)
    itemid: str = ""
    docname: str = ""
