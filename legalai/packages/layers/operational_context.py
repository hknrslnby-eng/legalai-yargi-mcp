"""Cautious, deterministic operational and sector context hypotheses."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from collections.abc import Mapping, Sequence
from legalai.packages.layers.operational_lenses import OperationalFinding, build_operational_findings


def _normalized(value: str) -> str:
    return (
        value.casefold()
        .replace("ü", "u")
        .replace("ı", "i")
        .replace("ş", "s")
        .replace("ğ", "g")
        .replace("ö", "o")
        .replace("ç", "c")
    )


@dataclass(frozen=True)
class OperationalContext:
    domain: str | None
    hypotheses: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    items: tuple[dict[str, str], ...] = ()
    safety_note: str = "Bu operasyonel çerçeve kesin olgu değildir; somut delil ile doğrulanmalıdır."

    findings: tuple[OperationalFinding, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["hypotheses"] = list(self.hypotheses)
        payload["unknowns"] = list(self.unknowns)
        payload["items"] = [dict(item) for item in self.items]
        payload["findings"] = [
            {
                "domain": item.domain,
                "label": item.label,
                "statement": item.statement,
                "evidence_status": item.evidence_status,
                "legal_impacts": list(item.legal_impacts),
                "confidence": item.confidence,
            }
            for item in self.findings
        ]
        return payload


class OperationalContextBuilder:
    """Infer only cautious, reviewable operational context from the prompt."""

    def build(
        self, question: str, jurisdiction_ids: Sequence[str] = (),
        known_facts: Mapping[str, Any] | None = None, documents: Sequence[Any] = (),
    ) -> OperationalContext:
        normalized = _normalized(question or "")
        jurisdictions = {_normalized(value) for value in jurisdiction_ids}
        findings, _operational_unknowns = build_operational_findings(
            question=question, known_facts=known_facts, jurisdiction_ids=jurisdiction_ids, documents=documents,
        )
        crypto_signal = any(
            token in normalized
            for token in ("kripto", "cuzdan", "blockchain", "sanal para", "stablecoin")
        )
        if crypto_signal:
            hypotheses = (
                "İşlem zinciri, cüzdan kontrolü ve üçüncü kişi yönlendirmesi incelenmelidir.",
                "Zararın oluşumu, geri döndürülebilirlik ve platform kayıtları ayrıca doğrulanmalıdır.",
            )
            unknowns = (
                "Cüzdan sahibi, transfer onayı, platform kayıtları ve teknik işlem zaman çizelgesi bilinmiyor.",
            )
            items = tuple(
                {"label": "operasyonel hipotez", "text": item} for item in hypotheses
            ) + tuple(
                {"label": "doğrulama gerekli", "text": item} for item in unknowns
            )
            return OperationalContext(
                domain="crypto_asset_operations",
                hypotheses=hypotheses,
                unknowns=unknowns,
                items=items,
                findings=findings,
            )

        if "rekabet" in normalized or "dagitim" in normalized or "tedarik" in normalized:
            hypotheses = (
                "Ürün/hizmet, tedarik veya dağıtım akışının pazar etkisi somut verilerle incelenmelidir.",
            )
            unknowns = ("İlgili ürün pazarı, coğrafi pazar ve ticari uygulama verileri eksik olabilir.",)
            items = tuple(
                {"label": "operasyonel hipotez", "text": item} for item in hypotheses
            ) + tuple(
                {"label": "doğrulama gerekli", "text": item} for item in unknowns
            )
            return OperationalContext(
                domain="commercial_market_operations",
                hypotheses=hypotheses,
                unknowns=unknowns,
                items=items,
                findings=findings,
            )

        note = (
            "İlgili operasyonel bağlam somut girdiden ayrıştırılamadı; sektör veya iş akışı bilgisi doğrulanmalı."
        )
        return OperationalContext(
            domain=None,
            unknowns=(note,),
            findings=findings,
            items=({"label": "doğrulama gerekli", "text": note},),
        )
