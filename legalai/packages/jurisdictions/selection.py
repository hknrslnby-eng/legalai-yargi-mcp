"""Çoklu hukuk alanı ve alt uzmanlık seçimi."""
from __future__ import annotations

from dataclasses import dataclass, field

from legalai.packages.jurisdictions.keywords import JURISDICTION_KEYWORDS
from legalai.packages.layers.related_law_selection import RelatedLawSelection, select_related_law_domains


_LENS_KEYWORDS: dict[str, tuple[str, ...]] = {
    "sozlesmeler": ("sözleşme", "fesih", "cezai şart"),
    "kira": ("kira", "kiracı", "kiraya veren"),
    "tazminat": ("tazminat", "haksız fiil", "zararın giderimi"),
    "haksiz_rekabet": ("haksız rekabet", "ticari itibar", "iltibas"),
    "marka": ("marka", "marka hakkı"),
    "patent": ("patent", "buluş"),
    "ticaret": ("ticaret", "şirket", "ticari iş"),
    "gumruk_hukuku": ("gümrük", "gtip", "menşe", "gümrük vergisi"),
    "dis_ticaret": ("dış ticaret", "ithalat", "ihracat"),
    "vergi_hukuku": ("vergi", "tarife", "telafi edici vergi"),
    "urun_gtip": ("gtip", "hs code", "benzer mal", "ürün", "menşe"),
    "dto_hukuku": ("dtö", "wto", "anti-dumping agreement", "scm agreement", "safeguards agreement"),
    "ab_ticaret_hukuku": ("ab ticaret", "dg trade", "2016/1036", "2016/1037", "2015/478"),
    "abd_trade_remedy": ("usdoc", "usitc", "tariff act", "title vii", "trade remedy"),
}


@dataclass
class JurisdictionSelection:
    primary: str
    supporting: list[str] = field(default_factory=list)
    expert_lenses: list[str] = field(default_factory=list)
    confidence: float = 0.0
    assumptions: list[str] = field(default_factory=list)
    scores: dict[str, int] = field(default_factory=dict)
    related_law: RelatedLawSelection | None = None


def _score_question(question: str) -> dict[str, int]:
    lowered = question.lower()
    return {
        jid: hits
        for jid, keywords in JURISDICTION_KEYWORDS.items()
        if (hits := sum(1 for keyword in keywords if keyword.lower() in lowered))
    }


def _detect_lenses(question: str) -> list[str]:
    lowered = question.lower()
    return [
        lens
        for lens, keywords in _LENS_KEYWORDS.items()
        if any(keyword.lower() in lowered for keyword in keywords)
    ]


def guess_jurisdictions(question: str) -> JurisdictionSelection:
    scores = _score_question(question)
    lenses = _detect_lenses(question)
    if not scores:
        result = JurisdictionSelection(
            primary="diger",
            expert_lenses=lenses,
            assumptions=["Soruda belirli bir hukuk alanı güvenle tespit edilemedi."],
        )
        result.related_law = select_related_law_domains(question=question, primary_domain=result.primary, expert_lenses=lenses)
        return result

    primary = max(scores, key=lambda jid: scores[jid])
    top_score = scores[primary]
    supporting = [
        jid for jid, score in scores.items()
        if jid != primary and score >= max(1, top_score - 1)
    ]
    confidence = top_score / sum(scores.values())
    result = JurisdictionSelection(
        primary=primary,
        supporting=supporting,
        expert_lenses=lenses,
        confidence=round(confidence, 3),
        scores=scores,
    )
    result.related_law = select_related_law_domains(
        question=question,
        primary_domain=primary,
        supporting_domains=supporting,
        expert_lenses=lenses,
    )
    return result
